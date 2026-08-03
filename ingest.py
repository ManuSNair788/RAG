import os
import requests
from bs4 import BeautifulSoup
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from dotenv import load_dotenv

load_dotenv()

# List of the 10 selected Groww AMC URLs
AMC_URLS = [
    "https://groww.in/mutual-funds/amc/nj-mutual-funds",
    "https://groww.in/mutual-funds/amc/abakkus-mutual-funds",
    "https://groww.in/mutual-funds/amc/choice-mutual-funds",
    "https://groww.in/mutual-funds/amc/the-wealth-company-mutual-funds",
    "https://groww.in/mutual-funds/amc/capitalmind-mutual-funds",
    "https://groww.in/mutual-funds/amc/jioblackrock-mutual-funds",
    "https://groww.in/mutual-funds/amc/unifi-mutual-funds",
    "https://groww.in/mutual-funds/amc/helios-mutual-funds",
    "https://groww.in/mutual-funds/amc/bajaj-finserv-mutual-funds",
    "https://groww.in/mutual-funds/amc/navi-mutual-funds",
]

CHROMA_DB_DIR = "./chroma_db"

def scrape_url(url):
    """Scrapes the main text content from a given URL."""
    try:
        response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract title
        title = soup.title.string if soup.title else "Unknown Title"
        
        # Extract text (removing scripts and styles for cleaner text)
        for script in soup(["script", "style"]):
            script.extract()
        
        text = soup.get_text(separator=' ', strip=True)
        return text, title
    except Exception as e:
        print(f"Failed to scrape {url}: {e}")
        return None, None

def ingest_data():
    """Main function to scrape, chunk, and embed data into ChromaDB."""
    print("Starting data ingestion process...")
    
    docs = []
    metadatas = []
    
    # 1. Scrape Data
    for url in AMC_URLS:
        print(f"Scraping: {url}")
        text, title = scrape_url(url)
        if text:
            docs.append(text)
            # Store the URL as metadata to ensure exact citation matching later
            metadatas.append({"source": url, "title": title})
            
    if not docs:
        print("No data scraped. Exiting.")
        return
        
    # 2. Chunk Text
    print("Chunking text...")
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
        separators=["\n\n", "\n", ".", " ", ""]
    )
    
    chunked_docs = []
    chunked_metadatas = []
    
    for i, doc in enumerate(docs):
        chunks = text_splitter.split_text(doc)
        for chunk in chunks:
            chunked_docs.append(chunk)
            chunked_metadatas.append(metadatas[i])
            
    print(f"Created {len(chunked_docs)} chunks from {len(docs)} pages.")

    # 3. Create Embeddings and Store in VectorDB
    print("Initializing embedding model...")
    # Requires GEMINI_API_KEY to be set in the .env file
    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
    
    print("Storing embeddings in ChromaDB (this may take a moment)...")
    vector_db = Chroma.from_texts(
        texts=chunked_docs,
        embedding=embeddings,
        metadatas=chunked_metadatas,
        persist_directory=CHROMA_DB_DIR
    )
    
    print(f"Successfully ingested data into ChromaDB at {CHROMA_DB_DIR}")

if __name__ == "__main__":
    ingest_data()
