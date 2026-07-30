import os
import streamlit as st
from dotenv import load_dotenv
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_chroma import Chroma
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from langchain_core.output_parsers import StrOutputParser

# import chromadb

load_dotenv()

if "GEMINI_API_KEY" in st.secrets:
    os.environ["GEMINI_API_KEY"] = st.secrets["GEMINI_API_KEY"]

def get_oracle_response(query: str, response_length: str = "medium", category: str = "general"):

    if not response_length:
        response_length = "medium"

    if not category:
        category = "general"

    embeddings = GoogleGenerativeAIEmbeddings(
        model = "gemini-embedding-001",
        task_type = "retrieval_query",
        # output_dimensionality = 3072
    )

    vector_db = Chroma(
        persist_directory="src/ibm_oracle_db",
        embedding_function=embeddings
    )

    retriever = vector_db.as_retriever(search_kwargs={"k": 5})

    template = [
        ("system", "You are an IBM Licensing expert who has been contracted to answer queries with regards to IBM software and its licensing. Use only the provided context to answer. You will receive inputs from the user such as the response length and the category of query: {category} to help you tailor your response"
                    "Give your answer according to the requested length: {response_length}; If the user desires a summarized answer, use no more than 100 words, If the answer length is medium, then use no more than 300 words and if the answer length is long, then use no more than 500 words. However, ensure that the provided output answers the user's query."
                    "If the answer is not in the context, state the following verbatim 'the information is not available'"
                    "Always cite the source and page number in a pretty and human readable format, however NEVER reveal the folder structure etc. of the retrived information, just the name of the document and the page number (use markdown)."),
        ("human", "Context:\n{context}\n\nQuestion: {question} \n\n Answer length desired: {response_length}")
    ]
    prompt = ChatPromptTemplate.from_messages(template)

    llm = ChatGoogleGenerativeAI(model="gemini-3-flash-preview", temperature=0.1)

    def format_docs(docs):
        return "\n\n".join(
            f"--- START CHUNK ---\n"
            f"Source: {d.metadata.get('source')}\n"
            f"Page: {d.metadata.get('page')}\n"
            f"Content: {d.page_content}\n"
            f"--- END CHUNK ---"
            for d in docs
        )

    rag_chain = (
        {
            "context": (lambda x: x['question']) | retriever | format_docs,
            "response_length": (lambda x: x['response_length']),
            "question": (lambda x: x['question']),
            "category": (lambda x: x['category'])
        }
        | prompt
        | llm
        | StrOutputParser()
    )

    response = rag_chain.invoke({
        "question": query,
        "response_length": response_length,
        "category": category
    })
    # print(vector_db)
    source_documents = retriever.invoke(query)
    
    return response, source_documents

# if __name__ == "__main__":
    
    # client = chromadb.PersistentClient(path="ibm_oracle_db")
    # collections = client.list_collections()
    # print(collections)
    # for col in collections:
    #     print(f"Name: {col.name}, Count: {col.count()}")

    # # Test Question
    # ans, docs = get_oracle_response("What is the definition of ILMT?")
    # print(f"\nORACLE RESPONSE:\n{ans}")