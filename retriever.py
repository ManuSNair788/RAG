"""
retriever.py - Phase 4: Retrieval & Synthesis (RAG Pipeline)

This module handles:
1. Semantic search over ChromaDB to retrieve relevant factual chunks.
2. Generating answers using Groq (llama-3.3-70b-versatile) based purely on retrieved context.
3. Strict enforcement of Groq rate limits (30 RPM, 12k TPM) by limiting retrieved chunks and prompt length.
4. Outputting citations and footers.
"""

import os
import json
import chromadb
from datetime import datetime
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate
from chromadb.utils import embedding_functions

# Load environment variables
load_dotenv()

# Constants
CHROMA_DB_DIR = "./chroma_db/"
COLLECTION_NAME = "groww_mutual_funds"
EMBEDDING_MODEL = "BAAI/bge-small-en-v1.5"
LLM_MODEL = "llama-3.3-70b-versatile"
MAX_RESULTS = 3 # Strict Top-K to save tokens for Groq limit (12k TPM)

# Strict System Prompt to enforce facts and 3-sentence limits
# Made token-efficient to conserve limits
RAG_PROMPT = """You are a highly restricted AI assistant for Groww Mutual Funds.
Your only job is to answer the user's question using the provided Context.
Rules:
1. NEVER hallucinate. If the answer is not in the context, say: "I'm sorry, I don't have that information."
2. Keep your answer under 3 sentences. Be concise.
3. NEVER provide investment advice or predict performance.

Context:
{context}

Question: {question}

Answer:"""

class RAGPipeline:
    def __init__(self):
        """Initializes vector DB connection and LLM client."""
        # Setup ChromaDB
        self.chroma_client = chromadb.PersistentClient(path=CHROMA_DB_DIR)
        self.embedder = embedding_functions.SentenceTransformerEmbeddingFunction(model_name=EMBEDDING_MODEL)
        self.collection = self.chroma_client.get_collection(
            name=COLLECTION_NAME, 
            embedding_function=self.embedder
        )
        
        # Setup Groq LLM
        # Catching token limits via configuration
        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY not found in environment.")
            
        self.llm = ChatGroq(
            model_name=LLM_MODEL, 
            temperature=0,      # Zero creativity for pure facts
            max_tokens=150      # Limit output to save tokens (approx 3 sentences)
        )
        self.prompt = PromptTemplate.from_template(RAG_PROMPT)
        self.chain = self.prompt | self.llm

    def search(self, query: str, top_k: int = MAX_RESULTS) -> list:
        """Retrieves top-k relevant chunks from the vector database."""
        # Simple similarity search without metadata pre-filtering for now, 
        # though we can easily inject it via 'where' clause if we extract entities.
        results = self.collection.query(
            query_texts=[query],
            n_results=top_k
        )
        
        chunks = []
        if results['documents'] and results['documents'][0]:
            for doc, meta in zip(results['documents'][0], results['metadatas'][0]):
                chunks.append({
                    "text": doc,
                    "metadata": meta
                })
        return chunks

    def generate_answer(self, query: str) -> dict:
        """Runs the full RAG pipeline and returns the answer with citations."""
        try:
            # 1. Retrieve
            chunks = self.search(query)
            
            if not chunks:
                return {
                    "answer": "I couldn't find any relevant information in my database.",
                    "citation": None,
                    "error": False
                }
                
            # 2. Build Context String
            context_text = "\n\n".join([f"- {c['text']}" for c in chunks])
            
            # 3. Generate Answer via LLM
            response = self.chain.invoke({
                "context": context_text,
                "question": query
            })
            
            final_answer = response.content.strip()
            
            # 4. Extract Primary Citation
            # We cite the first retrieved chunk as the primary source
            primary_source = chunks[0]["metadata"].get("source", "Groww Mutual Funds")
            today_date = datetime.now().strftime("%B %d, %Y")
            
            return {
                "answer": final_answer,
                "citation": primary_source,
                "footer": f"Last updated from sources: {today_date}",
                "error": False
            }
            
        except Exception as e:
            error_msg = str(e).lower()
            if "rate_limit_exceeded" in error_msg or "429" in error_msg:
                # Graceful degradation for Groq rate limits (12k TPM, 30 RPM)
                return {
                    "answer": "We are experiencing high traffic right now and have temporarily hit our rate limits. Please wait a minute and try again.",
                    "citation": None,
                    "error": True
                }
            else:
                print(f"Internal Error: {e}")
                return {
                    "answer": "An internal error occurred while processing your query.",
                    "citation": None,
                    "error": True
                }

if __name__ == "__main__":
    # Test the retriever
    import sys
    if sys.stdout.encoding != 'utf-8':
        try: sys.stdout.reconfigure(encoding='utf-8')
        except AttributeError: pass
        
    print("Initializing RAG Pipeline...")
    rag = RAGPipeline()
    
    test_queries = [
        "What is the expense ratio of Navi Nifty 50 Index Fund?",
        "Who is the fund manager for Bajaj Finserv Flexi Cap Fund?"
    ]
    
    for q in test_queries:
        print(f"\nQuery: {q}")
        result = rag.generate_answer(q)
        print(f"Answer: {result['answer']}")
        if result['citation']:
            print(f"Source: {result['citation']}")
            print(f"Footer: {result['footer']}")
        if result['error']:
            print("ERROR OCCURRED.")
        print("-" * 50)
