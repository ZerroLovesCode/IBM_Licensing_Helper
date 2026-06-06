import os
from dotenv import load_dotenv
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_chroma import Chroma
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

# import chromadb

load_dotenv()

def get_oracle_response(query: str):
    embeddings = GoogleGenerativeAIEmbeddings(
        model = "gemini-embedding-001",
        task_type = "retrieval_query",
        # output_dimensionality = 3072
    )

    vector_db = Chroma(
        persist_directory="ibm_oracle_db",
        embedding_function=embeddings
    )

    retriever = vector_db.as_retriever(search_kwargs={"k": 5})

    template = [
        ("system", "You are an IBM Licensing expert who has been contracted to answer queries with regards to IBM software and its licensing. Use only the provided context to answer. "
                    "If the answer is not in the context, state that clearly. "
                    "Always cite the source and page number."),
        ("human", "Context:\n{context}\n\nQuestion: {question}")
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
            "context": retriever | format_docs,
            "question": RunnablePassthrough()
        }
        | prompt
        | llm
        | StrOutputParser()
    )

    response = rag_chain.invoke(query)
    print(vector_db)
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