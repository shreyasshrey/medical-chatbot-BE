# Medical RAG Chatbot — Project Draft

## 1. Project Overview
Medical RAG Chatbot is a FastAPI-based backend that answers user medical questions using Retrieval-Augmented Generation (RAG). It retrieves relevant content from ingested PDF documents (stored in a persistent Chroma vector database) and uses an LLM (Hugging Face Router / Inference API) to generate answers grounded in retrieved context.

**Primary goals**
- Provide context-grounded medical Q&A (reduce hallucinations by using retrieved source context).
- Support session-based conversation with simple memory.
- Offer streaming-like responses for UI integration, while also supporting normal JSON responses for Swagger/testing.

## 2. Key Features
- **FastAPI REST API**
  - `POST /chat` for chat responses
  - `GET /health` for health checks
  - Swagger UI at `/docs`
- **RAG Pipeline**
  - Query rewriting (turn follow-up queries into standalone questions)
  - Semantic retrieval (Chroma vector similarity search)
  - Reranking (CrossEncoder)
  - Context assembly (top chunks stitched into final prompt)
- **PDF Ingestion**
  - CLI ingestion script to load PDFs into Chroma and persist to disk
- **Session Memory**
  - Simple in-memory storage keyed by `session_id`
- **Streaming + Non-streaming**
  - SSE token streaming mode (for frontends)
  - Non-streaming JSON mode (for Swagger/testing) returning:
    - `answer` (sentence/text)
    - `suggested_questions` (follow-up questions)

## 3. System Architecture

### High-level architecture
- Client (Swagger/UI) calls FastAPI `/chat`
- FastAPI builds RAG context using:
  - Memory (history)
  - Query rewriter (LLM)
  - Retriever (Chroma + embeddings)
  - Reranker (CrossEncoder)
- FastAPI generates response via LLM and returns:
  - SSE stream (if `stream=true`)
  - JSON (if `stream=false`)

### Logical diagram


### Data storage
- **Vector DB**: Chroma persistent store at `CHROMA_DIR` (default `./data/chroma_db`)
- **Conversation memory**: In-memory dict (clears on server restart)

## 4. Technology Stack
- **Backend API**: FastAPI, Uvicorn
- **Streaming**: `sse-starlette` (Server-Sent Events)
- **RAG / Orchestration**: LangChain integrations
- **Vector DB**: ChromaDB (`langchain_chroma`)
- **Embeddings**: `langchain_huggingface` (HuggingFaceEmbeddings)
- **Reranking**: `sentence-transformers` CrossEncoder (`BAAI/bge-reranker-large`)
- **PDF Loading**: `pypdf` via `langchain_community.document_loaders.PyPDFLoader`
- **Environment config**: `python-dotenv`

## 5. Setup and Usage

### Prerequisites
- Python 3.11+ recommended
- (Optional) Docker + Docker Compose
- Hugging Face token for Router/Inference APIs

### Install (Windows)
```powershell
cd d:\Gen-ai-projects\medical-rag-chatbot
python -m venv .venv
.venv\Scripts\activate.bat
pip install -r requirements.txt
```

### Environment variables
Create/update `.env` (do not commit real secrets):
- `HF_TOKEN` = Hugging Face access token
- `MODEL_NAME` = model id (default used in code: `Qwen/Qwen2.5-7B-Instruct`)
- `HF_API_URL` = optional override (default: `https://router.huggingface.co/v1/chat/completions`)
- `CHROMA_DIR` = optional override (default: `./data/chroma_db`)
- `EMBEDDING_MODEL` = optional override (default: `BAAI/bge-m3`)
- `TEMPERATURE`, `MAX_NEW_TOKENS`, `TOP_K_RETRIEVAL`, `TOP_K_RERANK`

### Ingest PDFs (build the vector DB)
Put PDFs under `data/pdfs/` and run:
```powershell
python scripts\ingest.py
```

### Run the API
```powershell
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

### Test in Swagger
- Open: `http://127.0.0.1:8000/docs`
- Use `POST /chat`

Example non-streaming request body (best for Swagger):
```json
{
  "question": "What is the function of the heart?",
  "session_id": "test-1",
  "stream": false
}
```

Example streaming request body (for a frontend that parses SSE):
```json
{
  "question": "What is the function of the heart?",
  "session_id": "test-1",
  "stream": true
}
```

## 6. Deployment

### Dockerfile deployment
- `Dockerfile` runs Uvicorn on port 8000.
- Ensure `.env` is available to the container (do not bake secrets into images).

### Docker Compose
`docker-compose.yml` starts:
- `api` service (FastAPI)
- `redis` service (currently optional; code uses in-memory memory by default)

Run:
```powershell
docker compose up --build
```

## Additional Important Points (Recommended)

### API Contract
- `POST /chat`
  - Request: `question`, `session_id`, `stream`
  - Response:
    - If `stream=true`: SSE stream of token events
    - If `stream=false`: JSON `{ "answer": "...", "suggested_questions": [...] }`
- `GET /health`: `{ "status": "ok" }`

### Limitations
- Memory is in-memory by default (lost on restart).
- “Streaming” is simulated by splitting a full LLM response into words.
- RAG grounding depends on ingestion quality and retrieval relevance.
- Reranker loads a large model and may increase startup/memory usage.

### Security Notes
- Never log or expose `HF_TOKEN`.
- Consider adding request rate limiting and input validation for production.
- Consider CORS configuration if serving a browser-based frontend.

### Troubleshooting
- If answers ignore PDFs, re-run ingestion and confirm `CHROMA_DIR` points to the persisted DB.
- If Hugging Face returns errors, verify:
  - `HF_TOKEN` is correct
  - `MODEL_NAME` is set
  - Network/proxy allows outbound HTTPS to Hugging Face