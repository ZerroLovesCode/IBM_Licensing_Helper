import streamlit as st

import os
from dotenv import load_dotenv
from typing import TypedDict, Annotated, Literal
from pydantic import Field, BaseModel

from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI

from langchain_chroma import Chroma

from langchain_core.messages import BaseMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.prompts import MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableConfig

from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.types import Command

load_dotenv()


# Utility functions:
def format_docs(docs):
    print("formatting documents...")
    return "\n\n".join(
        f"--- START CHUNK ---\n"
        f"Source: {d.metadata.get('source')}\n"
        f"Page: {d.metadata.get('page')}\n"
        f"Content: {d.page_content}\n"
        f"--- END CHUNK ---"
        for d in docs
)


# State that flows between the various nodes in the workflow.
class State(TypedDict):
    query: str 
    messages: Annotated[list[BaseMessage], add_messages] 

    needs_retrieval: bool
    retrieved_docs: str
    response: str


class RequiresRewrite(BaseModel):
    rewrite_required: bool = Field(description="True if the user's query is not a standalone query and requires more context from the conversation history, False otherwise")
    new_query: str = Field(description="The new query if a rewrite is required, if the query is standalone and does not require a rewrite, then this will be an empty string")

# Retrieve the relevant documents from the vector DB
def retrieve_chunks(state: State) -> dict:
    print("Retrieving documents...")
    embeddings = GoogleGenerativeAIEmbeddings(
        model = os.environ['GEMINI_EMBEDDING_MODEL'],
        task_type = "retrieval_query",
    )   

    vector_db = Chroma(
        persist_directory="src/ibm_oracle_db",
        embedding_function=embeddings
    )

    # The retriever must be aware of the conversation that happened so far because the query might depend on previous chat.
    query = state['query']
    rewriter_model = ChatGoogleGenerativeAI(
        model=os.environ['GEMINI_REWRITE_MODEL']
    ).with_structured_output(RequiresRewrite, method="json_schema")

    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are an agent that rewrites a query asked by a human if it depends on the prior conversation history between the human and the AI. The main purpose behind doing this is to ensure that the retriever in the RAG system has enough context to understand the query properly and perform semantic search. If the query does NOT require additional context (that is, it is a standalone query), don't return a rewritten query. You will return 2 things, (1) whether the query requires a rewrite and (2) the rewritten query including the relevant context from the previous conversation history if a rewrite is required"),
        (MessagesPlaceholder("messages")),
        ("human", "Query: {query}")
    ])
    rewriter_response = (prompt | rewriter_model).invoke({
        "query": query,
        "messages": state['messages']
    })
    if rewriter_response.rewrite_required:
        query = rewriter_response.new_query

    retriever = vector_db.as_retriever(search_kwargs = {"k": 5})
    documents = (retriever | format_docs).invoke(query)
    return {
        "retrieved_docs": documents
    }

# use the LLM along with the context from the vector db to generate a response
def generate_response(state: State) -> dict:
    #  Have two different prompts depending of if we have retrieved chunks...
    print(f"Generating response...using model {os.environ["GEMINI_GENERATION_MODEL"]}")

    if state['needs_retrieval']:
        template = [
            ("system", "You are an IBM Licensing expert who has been contracted to answer queries with regards to IBM software and its licensing. Use only the provided context to answer."
            "If the answer is not in the context, state the following verbatim 'The information is not available'"
            "Always cite the source and page number in a pretty and human readable format, however NEVER reveal the folder structure etc. of the retrived information, just the name of the document and the page number (use markdown)."),
            (MessagesPlaceholder("messages")),
            ("human", "Context:\n{retrieved_docs}\n\nQuestion: {query}")
        ]
    else:
        template = [
            ("system", "You are an IBM Licensing expert who has been contracted to answer queries with regards to IBM software and its licensing. Ask the user how you can help with their query. Let the user know that you can ONLY help with queries that are relevant to IBM licensing. You will be provided the chat history and the query"
            ),
            (MessagesPlaceholder("messages")),
            ("human", "Query: {query}")
        ]


    prompt = ChatPromptTemplate.from_messages(template)
    
    llm = ChatGoogleGenerativeAI(model=os.environ["GEMINI_GENERATION_MODEL"], temperature=0.1)
    response = (prompt | llm | StrOutputParser()).invoke(state)
    return {
        "response": response
        }


class Classifier_output(BaseModel):
    classifier_result: bool = Field(description="True if the given query is related to IBM licensing, False otherwise")

def needs_retrieval(state: State) -> Command[Literal["generate_response", "retrieve_chunks"]]:
    query = state["query"]
    classifier = ChatGoogleGenerativeAI(model=os.environ["GEMINI_CLASSIFIER_MODEL"], temperature=0).with_structured_output(Classifier_output, method="json_schema")

    template = [
        ("system", "You are a classifier who classifies whether the given query is related to IBM licensing or some IBM product. You will also be given a conversation history, which may be relevant in deciding the classification. You will only output either True (If the query is indeed related to IBM licensing or relevant to IBM licensing) or False (If the query has nothing to do with IBM licensing or relevant to IBM licensing)"),
        (MessagesPlaceholder("messages")),
        ("human", "Query: {query}")
    ]
    prompt = ChatPromptTemplate.from_messages(template)
    response = (prompt | classifier).invoke(
        {
            "query": query,
            "messages": state["messages"]
        }
    )
    return Command(
        update={
            "needs_retrieval": response.classifier_result
        },
        goto="retrieve_chunks" if response.classifier_result else "generate_response"
    )
# This function is required for integration with LangSmith and also to centralize workflow updates
def make_graph(config: RunnableConfig):
    graph = StateGraph(State)
    graph.add_node("needs_retrieval", needs_retrieval)
    graph.add_node("retrieve_chunks", retrieve_chunks)
    graph.add_node("generate_response", generate_response)

    # graph.add_conditional_edges(
    #     START,
    #     needs_retrieval,
    #     {
    #        True: "retrieve_chunks",
    #        False: "generate_response" 
    #     }
    # )
    graph.add_edge(START, "needs_retrieval")
    # graph.add_edge("needs_retrieval", "retrieve_chunks")
    # graph.add_edge("needs_retrieval", "generate_response")
    # graph.add_edge(START, "retrieve_chunks")
    graph.add_edge("retrieve_chunks", "generate_response")
    graph.add_edge("generate_response", END)

    wf = graph.compile()
    return wf


def workflow(message_history: list[BaseMessage], query: str):
    print("Starting the workflow...")
    
    wf = make_graph({})
    res = wf.stream({
        "messages": message_history,
        "query": query,
    }, stream_mode="messages")
    return res

# if __name__ == "__main__":
    
    # client = chromadb.PersistentClient(path="ibm_oracle_db")
    # collections = client.list_collections()
    # print(collections)
    # for col in collections:
    #     print(f"Name: {col.name}, Count: {col.count()}")

    # # Test Question
    # ans, docs = get_oracle_response("What is the definition of ILMT?")
    # print(f"\nORACLE RESPONSE:\n{ans}")