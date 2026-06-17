# Medical RAG Chatbot — Backend

A FastAPI backend that answers **medical questions grounded in your own PDF documents**
using a Retrieval-Augmented Generation (RAG) pipeline. It retrieves relevant passages
from a vector database, re-ranks them, and asks an LLM to answer **using only that context**.

---

## Tech Stack

| Layer              | Technology                                        |
| ------------------ | ------------------------------------------------- |
| API / Server       | FastAPI + Uvicorn                                 |
| Vector Database    | ChromaDB (persisted to `data/chroma_db/`)         |
| Embeddings         | HuggingFace `BAAI/bge-m3`                          |
| Reranker           | Cross-encoder `BAAI/bge-reranker-large`           |
| LLM                | `Qwen/Qwen2.5-7B-Instruct` via HuggingFace router |
| Conversation Memory| In-memory dict (Redis implementation included, commented) |
| PDF Loading        | LangChain `PyPDFLoader`                           |
| Containerization   | Docker + Docker Compose                           |

---

## Project Structure

```
.
├── app/
│   ├── main.py                # FastAPI entrypoint — creates `app`, mounts router, /health
│   ├── api/
│   │   └── routes.py          # POST /chat — orchestrates the whole request
│   ├── core/
│   │   ├── config.py          # Loads .env settings (models, Chroma dir, top-k, etc.)
│   │   └── prompts.py         # RAG prompt template
│   ├── schemas/
│   │   └── chat.py            # ChatRequest model (question, session_id, stream)
│   └── services/
│       ├── rag.py             # build_context() — the RAG orchestrator
│       ├── retriever.py       # semantic_search() — vector similarity search
│       ├── reranker.py        # rerank() — cross-encoder re-scoring
│       ├── query_rewriter.py  # rewrite() — follow-up → standalone question
│       ├── embeddings.py      # bge-m3 embedding model
│       ├── vector_store.py    # Chroma vector DB instance
│       ├── llm.py             # call_llm() — HuggingFace API call
│       ├── streaming.py       # stream_response() — word-by-word SSE streaming
│       └── memory.py          # get_history() / save_message() — chat history
├── scripts/
│   └── ingest.py              # PDF loader — builds the vector DB (run offline)
├── data/
│   ├── pdfs/                  # Source PDFs go here
│   └── chroma_db/             # Generated vector store (created by ingestion)
├── .env                       # Environment variables (DO NOT COMMIT)
├── requirements.txt
├── Dockerfile
└── docker-compose.yml
```

---

## How It Works

There are **two separate execution paths**. They do not run at the same time.

### 1. Ingestion (offline — run once per document set)

This is the "PDF loader." It reads PDFs, splits them into chunks, embeds them,
and stores them in ChromaDB so they can be searched later.

**Entry point:** `scripts/ingest.py` → `main()`

```
scripts/ingest.py
  → PyPDFLoader            loads each PDF from data/pdfs/
  → RecursiveCharacterTextSplitter   1000-char chunks, 200 overlap
  → vector_store.py (Chroma)
        → embeddings.py (bge-m3)     converts chunks to vectors
  → data/chroma_db/        persisted vector store
```

### 2. Serving (the live API)

**Entry point:** `app/main.py` → creates the `app` object that Uvicorn runs.

A `POST /chat` request flows through the system like this:

```
POST /chat ──► app/api/routes.py  (chat handler)
                  │
                  ▼
            app/services/rag.py → build_context()
                  │ 1. get_history()      (memory.py)        load past turns
                  │ 2. rewrite()          (query_rewriter → llm.py)  follow-up → standalone Q
                  │ 3. semantic_search()  (retriever → vector_store) top-10 chunks from Chroma
                  │ 4. rerank()           (reranker.py)      cross-encoder → keep top-5
                  │ 5. join chunks into a context string
                  ▼
            routes.py builds the prompt
                  │
        ┌─────────┴──────────────┐
   stream = true            stream = false
        │                        │
  streaming.py             llm.py call_llm()
  calls llm.py, then       returns structured JSON
  yields word-by-word      { answer, suggested_questions }
  over Server-Sent Events  (parsed + validated in routes.py)
        │                        │
        └─────────┬──────────────┘
                  ▼
            memory.py save_message()   store user + assistant turns
```

**Summary of file-to-file execution at request time:**
`routes.py → rag.py → {retriever, reranker, query_rewriter, memory} → llm.py / streaming.py → back to routes.py`

---

## Setup & Run

### Prerequisites
- Python 3.11+
- A valid HuggingFace token with access to the inference router
- (Optional) Docker & Docker Compose

### Commands

```bash
# 1. Create and activate a virtual environment
python -m venv venv
source venv/bin/activate            # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
#    Ensure .env has a valid HF_TOKEN (see Configuration below)

# 4. Run the PDF loader / ingestion  (run from the PROJECT ROOT)
python -m scripts.ingest                                  # uses default data/pdfs/
python -m scripts.ingest data/pdfs/ANATOMY_PHYSIOLOGY.pdf # or specific file(s)/folder(s)

# 5. Run the application
uvicorn app.main:app --reload                             # http://localhost:8000
#    Swagger docs: http://localhost:8000/docs
#    Health check: http://localhost:8000/health
```

### Run with Docker (replaces steps 1–5)

```bash
docker-compose up --build
```

This starts the API on port `8000` and a Redis container on port `6379`
(Redis is wired up in compose but the active memory backend is in-memory; see Notes).

---

## API
### Test in Swagger
- Open: `http://127.0.0.1:8000/docs`
- Use `POST /chat`

Request body:

```json
{
  "question": "What is the function of red blood cells?",
  "session_id": "user-123",
  "stream": true
}
```

- `stream: true`  → Server-Sent Events; tokens streamed word-by-word.
- `stream: false` → JSON response:

```json
{
  "answer": "...",
  "suggested_questions": ["...", "...", "..."]
}
```

If the answer is not found in the retrieved context, the assistant replies that it can
only answer questions related to the uploaded medical documents, and returns no suggestions.

### `GET /health`
Returns `{"status": "ok"}`.

---

## Configuration (`.env`)

| Variable          | Default                       | Description                          |
| ----------------- | ----------------------------- | ------------------------------------ |
| `MODEL_NAME`      | `Qwen/Qwen2.5-7B-Instruct`    | LLM used for generation              |
| `EMBEDDING_MODEL` | `BAAI/bge-m3`                 | Embedding model                      |
| `CHROMA_DIR`      | `./data/chroma_db`            | Vector store location                |
| `REDIS_HOST`      | `redis`                       | Redis host (only if Redis memory on) |
| `REDIS_PORT`      | `6379`                        | Redis port                           |
| `TEMPERATURE`     | `0.2`                         | LLM sampling temperature             |
| `MAX_NEW_TOKENS`  | `512`                         | Max tokens generated                 |
| `TOP_K_RETRIEVAL` | `10`                          | Chunks pulled from vector search     |
| `TOP_K_RERANK`    | `5`                           | Chunks kept after reranking          |
| `HF_TOKEN`        | _(required)_                  | HuggingFace API token                |

---

## Notes & Gotchas

- **Run ingestion as a module** (`python -m scripts.ingest`), not `python scripts/ingest.py`,
  so the `from app.services...` imports resolve from the project root.
- **Security:** `.env` contains a real `HF_TOKEN`. Add `.env` to `.gitignore`, never commit it,
  and rotate the token if it has already been shared.
- **First run is slow:** the embedding model (`bge-m3`) and reranker (`bge-reranker-large`)
  are downloaded from HuggingFace on first use and require disk space + RAM.
- **`vector_db.persist()`** in `ingest.py` is deprecated in recent `langchain_chroma`
  (Chroma auto-persists). If it raises `AttributeError`, remove that line.
- **Memory is in-memory** and resets when the server restarts. A Redis-backed implementation
  is included (commented out) in `app/services/memory.py` for production use.
- **CORS** is currently open to `http://localhost:3000` only (see `app/main.py`).
