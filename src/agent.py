import os
from dotenv import load_dotenv
from pathlib import Path
from functools import lru_cache
from typing import TypedDict, Annotated, Literal
from pydantic import Field, BaseModel

from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI

from langchain_chroma import Chroma

from langchain_core.messages import BaseMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.prompts import MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool

from langgraph.graph import StateGraph, MessagesState, START, END
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

# Creating a separate function to get the retriever so that it can be cached.
@lru_cache(maxsize=1)
def get_retriever():
    DB_DIR = Path(__file__).parent.resolve()
    if not (DB_DIR / "ibm_oracle_db").is_dir():
        raise FileNotFoundError("The vector database is not initialized, please run the ingestion script...")

    embeddings = GoogleGenerativeAIEmbeddings(
        model = os.environ['GEMINI_EMBEDDING_MODEL'],
        task_type = 'retrieval_query'
    )

    vector_db = Chroma(
        persist_directory = DB_DIR / "ibm_oracle_db", 
        embedding_function = embeddings
    )
    if not (vector_db.get(limit=1).get("ids")):
        raise RuntimeError("The database is empty, please run the ingestion script...")

    retriever = vector_db.as_retriever(search_kwargs = {"k":5})
    return retriever

@tool
def search_official_ibm_documentation(query: str) -> str:
    '''
    Retrieves relevant documentation chunks from the official IBM knowledge base (Vector Database) to answer queries that are relevant to IBM licensing.
    Use this tool when the user's query is specific to IBM licensing and requires grounding in official IBM documentation.

    Args:
        query: str = a self-contained search query; replace pronouns and references like 'it' or 'that option' with the actual product or concept from the conversation. This query will be used to search a vector database with the embedded documents.
    
    Returns:
        A string that contains the relevant chunks that are obtained after the search - Contains the content along with the metadata such as Source and Page Number. Each chunk will be separated by --- START CHUNK --- and --- END CHUNK --- 

    Do NOT use this if the query is NOT relevant to IBM software or Licensing.
    '''

    retriever = get_retriever()
    documents = (retriever | format_docs).invoke(query)
    return documents



# Build the model
llm = ChatGoogleGenerativeAI(model = os.environ["GEMINI_GENERATION_MODEL"], temperature = 0.1)

# define the chat node
def chat_node(state: MessagesState) -> dict:
    print(f"Generating response...using model {os.environ["GEMINI_GENERATION_MODEL"]}")

    system_prompt = [("system", "You are a helpful IBM licensing expert. If the user's query is not related to IBM Licensing, you will refuse to answer the query by stating 'I can only help with IBM licensing queries' verbatim.")]
    message_history = state["messages"]
    response = llm.invoke(system_prompt + message_history) 
    return {
        "messages": [response]
    }


builder = StateGraph(MessagesState)
builder.add_node("chat", chat_node)

builder.add_edge(START, "chat")
builder.add_edge("chat", END)

graph = builder.compile()

if __name__ == "main":
    prompt = {}
    prompt["messages"] = [("user", "What is PVU?")] 
    print(graph.invoke(prompt))

