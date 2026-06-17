# Code Working (Execution Flow + File Responsibilities)

This document explains the complete end-to-end flow from the React frontend through the FastAPI backend to the RAG/LLM components, with file names and function names.

---

## End-to-End Execution Flow

```
[React Frontend]
   │  User types question in Chat UI
   │  POST /chat  { question, session_id, stream }
   ▼
[FastAPI — app/main.py + app/api/routes.py]
   │  Routes request to chat() handler
   ▼
[RAG Pipeline — app/services/rag.py → build_context()]
   │
   ├─ 1. get_history(session_id)          → app/services/memory.py
   │       Returns prior messages for this session
   │
   ├─ 2. rewrite(question, history)       → app/services/query_rewriter.py
   │       Calls call_llm() to turn a follow-up into a standalone question
   │
   ├─ 3. semantic_search(standalone_q)    → app/services/retriever.py
   │       Runs similarity_search() on ChromaDB via app/services/vector_store.py
   │       (embeddings from app/services/embeddings.py — BAAI/bge-m3)
   │
   ├─ 4. rerank(standalone_q, docs)       → app/services/reranker.py
   │       CrossEncoder (BAAI/bge-reranker-large) re-scores and sorts docs
   │
   └─ 5. context = top-5 chunks joined
         Returns: (standalone_q, context, history)
   ▼
[Route handler builds prompt]
   │  Injects context + standalone_q into prompt template
   │
   ├── stream=true  → app/services/streaming.py → stream_response(prompt)
   │       Calls call_llm() once, splits into words, yields SSE tokens
   │       React frontend reads EventSource and renders tokens progressively
   │
   └── stream=false → call_llm(structured_prompt)   → app/services/llm.py
           LLM returns JSON { answer, suggested_questions }
           Parsed and returned as JSON response to React frontend
   ▼
[Memory update]
   │  save_message(session_id, "user", question)
   │  save_message(session_id, "assistant", answer)
   └─ → app/services/memory.py
```

---

## Offline: PDF Ingestion Flow

```
[data/pdfs/*.pdf]
   ▼
[scripts/ingest.py → main()]
   │  PyPDFLoader loads each PDF
   │  RecursiveCharacterTextSplitter chunks (size=1000, overlap=200)
   │  HuggingFaceEmbeddings embeds chunks   ← app/services/embeddings.py
   │  vector_db.add_documents(chunks)       ← app/services/vector_store.py
   └─ Persists to CHROMA_DIR (./data/chroma_db)
```

---

## React Frontend Flow (Planned)

```
[src/App.jsx]
   └─ renders <ChatWindow />

[src/components/ChatWindow.jsx]
   ├─ Maintains messages[] state
   ├─ Sends POST /chat via src/services/api.js
   │     { question, session_id, stream: true/false }
   ├─ stream=true:  opens EventSource, appends tokens to assistant bubble
   └─ stream=false: receives { answer, suggested_questions }, renders both

[src/services/api.js]
   ├─ chatStream(question, sessionId, onToken)   — SSE path
   └─ chatJSON(question, sessionId)              — JSON path

[src/components/SuggestedQuestions.jsx]
   └─ Renders follow-up question chips from suggested_questions[]
```

---

## File Responsibilities

| File | Role |
|---|---|
| `app/main.py` | FastAPI app creation, router include, `/health` |
| `app/api/routes.py` | `/chat` endpoint — streaming vs non-streaming logic, saves messages |
| `app/schemas/chat.py` | `ChatRequest` model (`question`, `session_id`, `stream`) |
| `app/core/config.py` | Loads `.env`, exports `MODEL_NAME`, `EMBEDDING_MODEL`, `CHROMA_DIR`, `TEMPERATURE`, `MAX_NEW_TOKENS`, `TOP_K_RETRIEVAL`, `TOP_K_RERANK` |
| `app/core/prompts.py` | `RAG_PROMPT` template (context + question → answer) |
| `app/services/rag.py` | Orchestrates full RAG pipeline: memory → rewrite → retrieve → rerank → assemble |
| `app/services/memory.py` | In-memory session store; `get_history`, `save_message`, `clear_memory` (Redis stub present) |
| `app/services/query_rewriter.py` | Calls `call_llm()` to rewrite follow-up into standalone question |
| `app/services/retriever.py` | `semantic_search()` — ChromaDB similarity search |
| `app/services/vector_store.py` | Initializes `vector_db` (LangChain Chroma wrapper, persistent) |
| `app/services/embeddings.py` | Initializes `HuggingFaceEmbeddings` (BAAI/bge-m3) |
| `app/services/reranker.py` | `CrossEncoder` reranking — `rerank(query, docs)` |
| `app/services/llm.py` | `call_llm(prompt)` — POSTs to HuggingFace Router/Inference API, parses response |
| `app/services/streaming.py` | `stream_response(prompt)` — simulated streaming (calls LLM once, yields word-by-word) |
| `scripts/ingest.py` | PDF → chunks → embeddings → Chroma (run once to build knowledge base) |

---

## Key Notes

### Streaming is simulated
`stream_response()` calls the LLM once and splits the full response word-by-word. True token streaming requires an LLM endpoint that supports SSE/chunked responses.

### Memory resets on restart
`memory.py` uses an in-memory dict. A Redis client is stubbed out in the same file and can be swapped in by updating `get_history` / `save_message` to use Redis.

### CORS required for React frontend
Add `CORSMiddleware` in `app/main.py` before deploying the React frontend:
```python
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:3000"], allow_methods=["*"], allow_headers=["*"])
```

---

## Configuration Reference (app/core/config.py)

| Variable | Default | Purpose |
|---|---|---|
| `MODEL_NAME` | `Qwen/Qwen2.5-7B-Instruct` | LLM model on HuggingFace |
| `EMBEDDING_MODEL` | `BAAI/bge-m3` | Embedding model for ChromaDB |
| `CHROMA_DIR` | `./data/chroma_db` | Persistent vector store path |
| `TEMPERATURE` | `0.3` | LLM sampling temperature |
| `MAX_NEW_TOKENS` | `512` | Max tokens in LLM response |
| `TOP_K_RETRIEVAL` | `10` | Chunks fetched from ChromaDB |
| `TOP_K_RERANK` | `5` | Top chunks kept after reranking |

---

## API Contract

### POST /chat
**Request**
```json
{ "question": "string", "session_id": "string", "stream": false }
```
**Response (stream=false)**
```json
{ "answer": "...", "suggested_questions": ["...", "...", "..."] }
```
**Response (stream=true)**
SSE stream of `{ event: "token", data: "<word>" }` events

### GET /health
```json
{ "status": "ok" }
```
