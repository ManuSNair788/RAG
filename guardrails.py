"""
guardrails.py - Phase 3: Guardrails & Compliance Layer

This module provides security, privacy, and compliance checks for user inputs.
It ensures that the RAG pipeline only processes safe, factual queries.

Components:
1. PII Filter: Blocks PAN, Aadhaar, Account Numbers, and OTPs.
2. Input Classifier: Categorizes queries as FACTUAL, ADVISORY, or UNRELATED.
3. Refusal Handler: Generates polite compliance refusal messages.
"""

import re
import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate

# Load environment variables
load_dotenv()

# --- 1. PII FILTER ---

# Regex patterns for Indian PII
PII_PATTERNS = {
    "PAN_CARD": r"[A-Z]{5}[0-9]{4}[A-Z]{1}",
    "AADHAAR_CARD": r"\b\d{4}\s?\d{4}\s?\d{4}\b",
    "ACCOUNT_NUMBER": r"\b\d{9,18}\b",  # Generic Indian bank account numbers
    "OTP": r"\b\d{4,6}\b(?![\w.-])"      # 4 to 6 digit standalone numbers
}

def contains_pii(text: str) -> bool:
    """Returns True if the text contains sensitive PII."""
    # We skip OTP check if the number is part of a year (e.g. 2024) or a valid fund NAV
    # A simple refinement is to only flag specific combinations, but for strict compliance:
    for name, pattern in PII_PATTERNS.items():
        if name == "OTP":
            # OTPs are tricky because 4 digit numbers could be years.
            # We look for keywords near the 4-6 digit number or just skip generic 4-digit numbers unless OTP is mentioned.
            if "otp" in text.lower() and re.search(r"\b\d{4,6}\b", text):
                return True
            continue
            
        if re.search(pattern, text, re.IGNORECASE):
            return True
            
    return False


# --- 2. INPUT CLASSIFIER ---

# We use the fast Llama-3-8b model on Groq for sub-second classification
CLASSIFIER_PROMPT = """
You are a compliance router for a Mutual Fund AI assistant.
Your job is to strictly classify the user's query into one of three categories:

1. FACTUAL: The user is asking for objective data about a mutual fund (e.g., NAV, expense ratio, AUM, fund manager, exit load).
2. ADVISORY: The user is asking for financial advice, recommendations, predictions, or asking if a fund is "good" or "bad". (e.g., "Where should I invest?", "Will this fund go up?", "Is this a good fund?")
3. UNRELATED: The query is not related to mutual funds or the provided context.

Respond with exactly ONE WORD (the category name). No other text.

Query: "{query}"
Category:"""

def classify_query(query: str) -> str:
    """Classifies the user query using a fast LLM call."""
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        print("Warning: GROQ_API_KEY not found. Falling back to keyword classification.")
        return fallback_keyword_classifier(query)
        
    try:
        # Use the fast llama 3.1 model for classification
        llm = ChatGroq(model_name="llama-3.1-8b-instant", temperature=0)
        prompt = PromptTemplate.from_template(CLASSIFIER_PROMPT)
        chain = prompt | llm
        
        response = chain.invoke({"query": query})
        category = response.content.strip().upper()
        
        if category in ["FACTUAL", "ADVISORY", "UNRELATED"]:
            return category
        return "FACTUAL" # Default safe fallback if model hallucinates
        
    except Exception as e:
        print(f"Classifier error: {e}. Falling back to keywords.")
        return fallback_keyword_classifier(query)

def fallback_keyword_classifier(query: str) -> str:
    """Simple regex/keyword based router if LLM fails."""
    query_lower = query.lower()
    
    advisory_keywords = [
        "should i", "recommend", "advice", "predict", "will it go up", 
        "best fund", "good investment", "safe to invest", "where to invest"
    ]
    
    for kw in advisory_keywords:
        if kw in query_lower:
            return "ADVISORY"
            
    return "FACTUAL"


# --- 3. REFUSAL HANDLER ---

def get_refusal_message(reason: str) -> str:
    """Returns a standardized compliance refusal message based on the reason."""
    if reason == "PII":
        return (
            "⚠️ **Privacy Warning:** For your security, please do not share sensitive personal information "
            "(like PAN, Aadhaar, account numbers, or OTPs) with this assistant. I cannot process this query."
        )
    elif reason == "ADVISORY":
        return (
            "🛑 **Regulatory Compliance Notice:** I am an AI assistant designed strictly to provide factual information "
            "about mutual funds. I am not a SEBI-registered advisor and cannot provide personalized financial advice, "
            "recommendations, or market predictions. Please consult a certified financial planner for investment advice."
        )
    elif reason == "UNRELATED":
        return (
            "I am specialized solely in answering questions about Groww Mutual Funds, including their NAVs, "
            "expense ratios, and structures. I cannot answer queries unrelated to this topic."
        )
    else:
        return "I am unable to process this request."


# --- MAIN PIPELINE INTEGRATION ---

def check_guardrails(query: str) -> dict:
    """
    Runs all guardrails on the query.
    Returns a dict: {"is_safe": bool, "message": str (if unsafe), "category": str}
    """
    # 1. Check PII
    if contains_pii(query):
        return {"is_safe": False, "message": get_refusal_message("PII"), "category": "PII"}
        
    # 2. Classify intent
    category = classify_query(query)
    
    if category == "ADVISORY":
        return {"is_safe": False, "message": get_refusal_message("ADVISORY"), "category": category}
    elif category == "UNRELATED":
        return {"is_safe": False, "message": get_refusal_message("UNRELATED"), "category": category}
        
    # Safe factual query
    return {"is_safe": True, "message": "", "category": "FACTUAL"}


if __name__ == "__main__":
    import sys
    # Reconfigure stdout to support emoji printing on Windows consoles
    if sys.stdout.encoding != 'utf-8':
        try:
            sys.stdout.reconfigure(encoding='utf-8')
        except AttributeError:
            pass

    # Simple manual tests
    test_queries = [
        "What is the expense ratio for Navi Nifty 50?",
        "Should I invest my life savings in Bajaj Flexi Cap?",
        "My PAN is ABCDE1234F, can you check my portfolio?",
        "Who won the cricket world cup in 2011?"
    ]
    
    print("Testing Guardrails...\n" + "="*40)
    for q in test_queries:
        print(f"Query: '{q}'")
        result = check_guardrails(q)
        print(f"Result: {result['is_safe']}")
        print(f"Category: {result['category']}")
        if not result['is_safe']:
            print(f"Refusal Message: {result['message']}")
        print("-" * 40)
