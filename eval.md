# Evaluation Strategy: Mutual Fund FAQ Assistant

This document outlines the evaluation metrics, criteria, and testing strategies for each phase of the implementation plan. Evaluating these phases ensures the RAG system remains compliant, highly accurate, and performs within acceptable limits.

## Phase 1: Environment Setup & Foundation

| Evaluation Metric | Description | Success Criteria | Testing Method |
| :--- | :--- | :--- | :--- |
| **Dependency Integrity** | Verifying all libraries (`langchain`, `langchain-groq`, `sentence-transformers`, `chromadb`) are installed and compatible. | No import errors on script launch. | Run a dry-run script importing all libraries. |
| **Environment Verification** | Ensuring secure loading of API keys. | `GROQ_API_KEY` is loaded securely without being hardcoded. | Automated unit test checking `os.getenv("GROQ_API_KEY")`. |

## Phase 2: Data Ingestion Pipeline

| Evaluation Metric | Description | Success Criteria | Testing Method |
| :--- | :--- | :--- | :--- |
| **Scraping Success Rate** | The percentage of the 10 selected Groww AMC URLs successfully scraped. | 100% of URLs return valid HTML text payloads. | Log HTTP response codes; assert `text_length > 0` for each URL. |
| **Chunking Consistency** | Verifying that the `RecursiveCharacterTextSplitter` respects the token/character limits. | 95%+ of chunks are within the 500-token threshold with 50-token overlap. | Histogram analysis of chunk lengths prior to embedding. |
| **Vector DB Completeness** | Validating that the ChromaDB stores the exact number of embedded chunks and metadata mappings. | `db.count()` matches `len(chunked_docs)`. Every chunk has a valid `source` URL in metadata. | Assert vector count and randomly sample metadata keys. |

## Phase 3: Guardrails & Compliance Layer

| Evaluation Metric | Description | Success Criteria | Testing Method |
| :--- | :--- | :--- | :--- |
| **PII Detection Recall** | The system's ability to catch sensitive information (PAN, Aadhaar, Account Numbers). | 99%+ Recall on synthetic datasets containing PII. | Pass 100 dummy queries with injected PII and measure block rate. |
| **Intent Classification Accuracy** | The accuracy of routing queries as "Factual", "Advisory", or "Performance". | > 95% accuracy in correctly identifying Advisory/Performance queries. | Run a golden dataset of 50 factual and 50 advisory queries through the classifier and generate a confusion matrix. |
| **Guardrail Latency** | The time taken to execute regex and classification checks before hitting the LLM. | < 50ms overhead per query. | Benchmark execution time using `time` module. |

## Phase 4: Retrieval & Synthesis (RAG Pipeline)

| Evaluation Metric | Description | Success Criteria | Testing Method |
| :--- | :--- | :--- | :--- |
| **Retrieval Hit Rate (Top-K)** | Measures if the chunk containing the exact factual answer is present in the Top-3 results returned by the BGE model. | > 85% Hit Rate for factual questions. | Evaluate using a RAG assessment framework (e.g., Ragas or TruLens) against a curated Q&A dataset. |
| **LLM Faithfulness** | Measures if the Groq LLM generated response is strictly derived from the retrieved context (No Hallucination). | 100% Faithfulness Score. No external facts introduced. | Use an LLM-as-a-judge approach (prompting a secondary LLM to verify if the answer exists in the context). |
| **Constraint Adherence** | Measures strict compliance with the 3-sentence maximum limit. | 100% compliance. | Programmatic evaluation: count `.` `?` `!` in the final string. |
| **Citation Accuracy** | Ensures the appended source URL directly matches the metadata of the context chunk used by the LLM. | Primary citation always matches the context `source` metadata. | Assert source URL matches `docs[0].metadata['source']`. |

## Phase 5: Minimal User Interface

| Evaluation Metric | Description | Success Criteria | Testing Method |
| :--- | :--- | :--- | :--- |
| **End-to-End Latency** | Total round-trip time from user submission to UI rendering. | < 3 seconds average response time. | Automated load testing (e.g., using Locust) simulating 10 concurrent users. |
| **Disclaimer Visibility** | Ensures the "Facts-only. No investment advice." disclaimer is rendered persistently. | Present and prominently styled in the DOM. | Automated UI testing using Streamlit testing framework. |
| **Formatting Validation** | Validates the proper markdown rendering of the mandatory footer string. | Footer "Last updated from sources: <date>" strictly matches required format. | Regex matching on the final rendered output component. |
