"""
api.py - FastAPI Backend for Mutual Fund AI

Serves the Stitch-designed frontend and exposes a `/chat` REST endpoint 
that routes through our Guardrails and RAG Pipeline.
"""

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import sys

# Ensure stdout encodes correctly on Windows
if sys.stdout.encoding != 'utf-8':
    try: sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError: pass

from guardrails import check_guardrails
from retriever import RAGPipeline

app = FastAPI(title="Wealth AI Assistant API")

# Initialize RAG Pipeline globally (Lazy Loaded)
rag = None

def get_rag():
    global rag
    if rag is None:
        print("Lazy-loading RAG Pipeline (this downloads the embedding model on first request)...")
        rag = RAGPipeline()
    return rag

class ChatRequest(BaseModel):
    query: str

class ChatResponse(BaseModel):
    answer: str
    citation: str | None = None
    footer: str | None = None
    is_safe: bool = True

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    query = request.query.strip()
    if not query:
        return ChatResponse(answer="Please enter a valid question.")

    # 1. Guardrails Check
    guardrail_result = check_guardrails(query)
    if not guardrail_result["is_safe"]:
        return ChatResponse(
            answer=guardrail_result["reason"],
            is_safe=False
        )
        
    # 2. Retrieve & Generate
    try:
        pipeline = get_rag()
        rag_result = pipeline.generate_answer(query)
        return ChatResponse(
            answer=rag_result["answer"],
            citation=rag_result.get("citation"),
            footer=rag_result.get("footer"),
            is_safe=True
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Mount static files (this serves index.html at the root)
app.mount("/", StaticFiles(directory="static", html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="127.0.0.1", port=8000, reload=True)
