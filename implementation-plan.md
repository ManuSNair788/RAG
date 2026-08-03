# Implementation Plan: Mutual Fund FAQ Assistant

This document outlines the phase-wise implementation plan for the Mutual Fund FAQ Assistant RAG system, based on the approved architecture.

## User Review Required
> [!IMPORTANT]
> Please review the phases below. Once approved, I will begin execution by creating tasks and starting to code.
> We need to decide on the core LLM provider (e.g., Groq, OpenAI) and the orchestrator (Langchain vs LlamaIndex) before writing code. I have assumed **LangChain**, **Groq API** for the LLM, and **BGE Model** for embeddings for this plan. Let me know if you prefer an alternative.

## Open Questions
- Do you have an API key ready for the chosen LLM (e.g., `GROQ_API_KEY`)?
- Are you comfortable proceeding with **Streamlit** for the minimal user interface?

## Proposed Changes

### Phase 1: Environment Setup & Foundation
- Initialize a Python project structure and virtual environment.
- Install necessary dependencies (`langchain`, `beautifulsoup4`, `chromadb`, `streamlit`, `langchain-groq`, `sentence-transformers`).
- Create a `.env` file template for API keys and configuration.

---

### Phase 2: Data Ingestion Pipeline (Offline)

To ensure modularity and maintainability, the ingestion pipeline will be divided into 3 distinct tasks:

**Task 2.1: Web Scraper & Raw Storage**
- Build a script (`scraper.py`) to scrape the specific Groww URLs for the 10 selected AMCs.
- Save the raw HTML content locally (e.g., in a `data/raw/` directory) to avoid re-fetching during testing and development.

**Task 2.2: Data Cleaner & Text Chunking**
- Build a processor (`chunker.py`) that reads the raw HTML and uses BeautifulSoup to parse the content.
- **Boilerplate Elimination**: Navigate directly to `div.layout-main` to skip nav bars, sidebar AMC/category lists, and footer SEO links — avoiding the ~60% of page text that is identical boilerplate across all pages.
- **Semantic Chunking Strategy** (instead of naive character-count splitting):
  - `amc_overview` — AMC name, AUM, number of schemes, age, and description paragraph.
  - `key_information` — Structured table extraction: incorporation date, sponsor, trustee, CIO, CEO, compliance officer, address.
  - `fund_data` — One chunk per fund from the main fund listing table (Name, Category, Risk, NAV, Expense Ratio, Returns, Fund Size, Exit Load). No data is split across chunk boundaries.
  - `fund_details` — Individual fund detail cards (min investment amount, AUM, 1Y returns).
  - `faq` — Q&A pairs extracted from JSON-LD structured data embedded in `<script>` tags.
- Each chunk includes rich metadata: `source` URL, `section` type, `amc_name`, and `fund_name` (where applicable).
- Output the chunked data into `data/processed/chunks.json` and human-readable review files into `data/review/`.

**Task 2.3: Embedding & Vector Storage**
- Build an indexer (`embedder.py`) that reads `data/processed/chunks.json`.
- **Embedding Model**: Use `BAAI/bge-small-en-v1.5` (33M params, 384-dim vectors) via `sentence-transformers`.
  - **Why BGE-small over BGE-large?** Our corpus is only 181 structured chunks (not long-form documents). Chunks are short key-value pairs (avg ~200 chars) with clear factual content. BGE-small achieves near-identical retrieval quality to BGE-large on structured, short-text corpora while being 10x faster on CPU. No GPU is required.
- **Vector Store**: Initialize a persistent local ChromaDB instance at `./chroma_db/`.
- Store each chunk's embedding along with its full metadata (`source`, `section`, `amc_name`, `fund_name`) for filtered retrieval.
- Store the chunk text in ChromaDB's `documents` field for direct retrieval without a separate lookup.

---

### Phase 3: Guardrails & Compliance Layer
- **Input Classifier:** Implement a lightweight function/router to classify incoming user queries (Factual vs. Advisory/Performance).
- **PII Filter:** Implement regex-based filters to block queries containing PAN, Aadhaar, account numbers, or OTPs.
- **Refusal Handler:** Create standard, polite refusal templates that redirect users appropriately (e.g., linking to official AMFI resources for advice, or the specific factsheet for performance queries).

---

### Phase 4: Retrieval & Synthesis (RAG Pipeline)
- **Semantic Retriever (Structured + Dense):** Connect to ChromaDB. Because our chunks have rich metadata (`amc_name`, `fund_name`, `section`), the retrieval strategy will combine dense vector search with optional metadata pre-filtering. To respect **Groq's TPM limits (12k Tokens Per Minute)**, we will strictly limit the retrieved context to **Top-3 chunks**.
- **Prompt Engineering:** Design an extremely token-efficient strict system prompt enforcing the 3-sentence limit, factual tone, and no-hallucination constraint to minimize input/output tokens.
- **LLM Integration:** Integrate `llama-3.3-70b-versatile` via Groq to generate answers.
- **Rate Limit Handling:** Implement robust `try-except` blocks to catch Groq RateLimitErrors (HTTP 429) and provide graceful UI degradation (e.g., "Rate limit exceeded. Please wait a minute before trying again."). This accounts for the 30 RPM and 12k TPM restrictions.
- **Citation Formatter:** Format the output to ensure exactly one primary citation link and the mandatory footer (`"Last updated from sources: <date>"`) are appended to the final response.

---

### Phase 5: Minimal User Interface
- **Streamlit App:** Develop a clean UI containing:
  - A friendly welcome message.
  - 3 clickable example factual questions.
  - A persistent, visible disclaimer: *"Facts-only. No investment advice."*
- **Integration:** Connect the Streamlit frontend to the backend query processing pipeline.

---

### Phase 6: Scheduling Component (Daily Data Ingestion)
- **Objective:** Ensure the RAG assistant always has the latest mutual fund data (NAVs, Expense Ratios) by automatically triggering the ingestion pipeline daily.
- **Workflow:** 
  - Create an orchestration script (`ingest.py` or similar) that runs the ingestion components in sequence: `scraper.py` -> `chunker.py` -> `embedder.py`.
- **Implementation Mechanism:** 
  - Use **GitHub Actions**. We will create a `.github/workflows/schedule.yml` file that defines a cron job.
  - Every 24 hours (e.g., at midnight UTC), the GitHub Action will spin up a runner, install the dependencies, execute the ingestion script to update the ChromaDB vector files, and automatically commit the fresh database back to the `main` branch.

## Verification Plan

### Automated Tests
- Simple assertions for the Input Guardrails to verify advisory queries trigger the correct refusal.
- Assertions for the PII Filter to verify sensitive strings are correctly blocked.

### Manual Verification
- Run the ingestion pipeline locally to confirm data is correctly populated in ChromaDB with URLs attached.
- Launch the Streamlit app locally and test various queries (factual, subjective, performance) to ensure end-to-end functionality, strict citation rules, and refusal handling work precisely as architected.
