import chromadb
from pprint import pprint

CHROMA_DB_DIR = "./chroma_db/"
COLLECTION_NAME = "groww_mutual_funds"

def view_embeddings():
    print(f"Connecting to ChromaDB at {CHROMA_DB_DIR}...")
    chroma_client = chromadb.PersistentClient(path=CHROMA_DB_DIR)
    
    try:
        collection = chroma_client.get_collection(name=COLLECTION_NAME)
    except Exception as e:
        print(f"Error: Could not find collection '{COLLECTION_NAME}'. Make sure embedder.py ran successfully.")
        return
        
    print(f"Collection '{COLLECTION_NAME}' loaded successfully.")
    print(f"Total documents in collection: {collection.count()}\n")
    
    # Fetch 2 sample chunks with their embeddings
    print("Fetching 2 sample chunks with their embeddings...\n")
    
    # include=['embeddings', 'documents', 'metadatas'] ensures we get the vector data too
    results = collection.get(
        limit=2,
        include=['embeddings', 'documents', 'metadatas']
    )
    
    if not results['ids']:
        print("Collection is empty!")
        return
        
    for i in range(len(results['ids'])):
        print("="*60)
        print(f"CHUNK ID : {results['ids'][i]}")
        print(f"METADATA : {results['metadatas'][i]}")
        print("-" * 60)
        print("DOCUMENT :")
        print(results['documents'][i])
        print("-" * 60)
        
        embedding = results['embeddings'][i]
        print(f"EMBEDDING (Vector dimensions: {len(embedding)}) :")
        # Print the first 5 and last 5 values of the embedding vector to keep it readable
        preview = [round(x, 4) for x in embedding[:5]] + ["..."] + [round(x, 4) for x in embedding[-5:]]
        print(f"{preview}")
        print("="*60 + "\n")
        
    print("If you want to test a semantic search, run:")
    print("results = collection.query(query_texts=['What is the NAV of Bajaj Flexi Cap?'], n_results=3)")

if __name__ == "__main__":
    view_embeddings()
