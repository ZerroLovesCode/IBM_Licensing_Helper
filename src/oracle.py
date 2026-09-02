import streamlit as st

import os
from dotenv import load_dotenv
from typing import TypedDict, Annotated

from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI

from langchain_chroma import Chroma

from langchain_core.messages import BaseMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.prompts import MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser

from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages

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


class State(TypedDict):
    query: str 
    response_length: str
    category: str

    retrieved_docs: str
    response: str
    messages: Annotated[list[BaseMessage], add_messages] 


# Retrieve the relevant documents from the vector DB
def retrieve_chunks(state: State) -> dict:
    print("Retrieving documents...")
    embeddings = GoogleGenerativeAIEmbeddings(
        model = "gemini-embedding-001",
        task_type = "retrieval_query",
    )   

    vector_db = Chroma(
        persist_directory="src/ibm_oracle_db",
        embedding_function=embeddings
    )

    retriever = vector_db.as_retriever(search_kwargs = {"k": 5})
    documents = (retriever | format_docs).invoke(state['query'])
    return {
        "retrieved_docs": documents
    }

# use the LLM along with the context from the vector db to generate a response
def generate_response(state: State) -> dict:
    print(f"Generating response...using model {os.environ["GEMINI_GENERATION_MODEL"]}")
    template = [
        ("system", "You are an IBM Licensing expert who has been contracted to answer queries with regards to IBM software and its licensing. Use only the provided context to answer."
        "If the answer is not in the context, state the following verbatim 'The information is not available'"
        "Always cite the source and page number in a pretty and human readable format, however NEVER reveal the folder structure etc. of the retrived information, just the name of the document and the page number (use markdown)."),
        (MessagesPlaceholder("messages")),
        ("human", "Context:\n{retrieved_docs}\n\nQuestion: {query}")
    ]
    prompt = ChatPromptTemplate.from_messages(template)
    
    llm = ChatGoogleGenerativeAI(model=os.environ["GEMINI_GENERATION_MODEL"], temperature=0.1)
    response = (prompt | llm | StrOutputParser()).invoke(state)
    return {
        "response": response
        }




def workflow(message_history: list[BaseMessage], query: str, response_length: str = "medium", category: str = "general"):
    print("Starting the workflow...")
    graph = StateGraph(State)
    graph.add_node("retrieve_chunks", retrieve_chunks)
    graph.add_node("generate_response", generate_response)

    graph.add_edge(START, "retrieve_chunks")
    graph.add_edge("retrieve_chunks", "generate_response")
    graph.add_edge("generate_response", END)

    wf = graph.compile()
    res = wf.stream({
        "messages": message_history,
        "query": query,
        "response_length": response_length,
        "category": category
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