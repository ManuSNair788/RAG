# Mutual Fund FAQ Assistant Tasks

- `[x]` Phase 1: Environment Setup & Foundation
  - `[x]` Initialize a Python project structure and virtual environment.
  - `[x]` Install necessary dependencies (`langchain`, `beautifulsoup4`, `chromadb`, `streamlit`, `langchain-groq`, `sentence-transformers`).
  - `[x]` Create a `.env` file template for API keys and configuration.

- `[ ]` Phase 2: Data Ingestion Pipeline (Offline)
  - `[ ]` **Web Scraper:** Build a script to scrape the specific Groww URLs for the 10 selected AMCs.
  - `[ ]` **Data Cleaner & Chunking:** Implement HTML parsing and text chunking (500 tokens, 50 overlap), preserving URL metadata.
  - `[ ]` **Embedding & Storage:** Initialize local ChromaDB. Generate dense embeddings for chunks and store with metadata.

- `[ ]` Phase 3: Guardrails & Compliance Layer
  - `[ ]` **Input Classifier:** Classify queries (Factual vs. Advisory/Performance).
  - `[ ]` **PII Filter:** Regex filters for PAN, Aadhaar, account numbers, OTPs.
  - `[ ]` **Refusal Handler:** Refusal templates redirecting users appropriately.

- `[ ]` Phase 4: Retrieval & Synthesis (RAG Pipeline)
  - `[ ]` **Semantic Retriever:** Connect to ChromaDB for Top-K relevance based on user query.
  - `[ ]` **Prompt Engineering:** Strict system prompt (3-sentence limit, factual tone, no hallucination).
  - `[ ]` **LLM Integration:** Integrate Groq LLM to generate answers purely based on context.
  - `[ ]` **Citation Formatter:** Ensure exactly one primary citation link and footer.

- `[ ]` Phase 5: Minimal User Interface
  - `[ ]` **Streamlit App:** Clean UI with welcome message, 3 clickable example questions, and persistent disclaimer.
  - `[ ]` **Integration:** Connect Streamlit frontend to backend query pipeline.
