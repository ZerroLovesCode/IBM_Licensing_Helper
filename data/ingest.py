import glob
import os
import time
from dotenv import load_dotenv
from langchain_pymupdf4llm import PyMuPDF4LLMLoader
from langchain_text_splitters import MarkdownTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma

load_dotenv()

DATA_DIR = "data/Licensing_documents"
DB_DIR = "ibm_oracle_db"

def ingest_data():
    pdfs = glob.glob(os.path.join(DATA_DIR, "*.pdf"))
    if not pdfs:
        print(f"No PDFs found in {DATA_DIR}. Please add your IBM guides.")
        return
    
    all_pages = []
    for path in pdfs:
        print(f"Processing: {os.path.basename(path)}")
        loader = PyMuPDF4LLMLoader(path, mode="page")
        all_pages.extend(loader.load())
    
    splitter = MarkdownTextSplitter(chunk_size=1000, chunk_overlap=150)
    chunks = splitter.split_documents(all_pages)
    print(f"Split {len(all_pages)} pages into {len(chunks)} chunks.")

    print("Generating Embeddings and saving to ChromaDB...")
    embeddings = GoogleGenerativeAIEmbeddings(
        model="gemini-embedding-001",
        task_type="RETRIEVAL_DOCUMENT"
    )

    vector_db = Chroma(
        persist_directory=DB_DIR,
        embedding_function=embeddings
    )
    batch_size = 20 
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i : i + batch_size]
        print(f"Ingesting batch {i//batch_size + 1} ({len(batch)} chunks)...")
        
        # Add the batch to the database
        vector_db.add_documents(batch)
        
        # Throttling: Wait 2 seconds between batches to stay under 100 RPM
        # This gives the API "room to breathe"
        time.sleep(10)

    print(f"Successfully ingested data inro {DB_DIR}")

if __name__ == "__main__":
    print("## Starting Process ##")
    ingest_data()

# embeddings = GoogleGenerativeAIEmbeddings(
#     model="gemini-embedding-001",
#     task_type="RETRIEVAL_DOCUMENT"
# )

# print(embeddings.embed_query("Does this even work?"))