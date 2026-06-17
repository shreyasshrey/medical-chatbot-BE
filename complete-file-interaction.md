main.py
   │
   ▼
routes.py
   │
   ▼
rag.py
   │
   ├──────────────────────────────┐
   │                              │
   ▼                              ▼

memory.py                   query_rewriter.py
   │                              │
   ▼                              ▼

MySQL                       llm.py
(chat history)

   │
   ▼

retriever.py
   │
   ▼

vector_store.py
   │
   ▼

ChromaDB
   │
   ▼

embeddings.py
(HuggingFace Embeddings)

   │
   ▼

reranker.py
(BAAI/bge-reranker-large)

   │
   ▼

rag.py
(Build Context)

   │
   ▼

routes.py
(Create Prompt)

   │
   ▼

llm.py
(HuggingFace LLM)

   │
   ▼

streaming.py
(Optional SSE)

   │
   ▼

memory.py
(Save Chat)

   │
   ▼

React Frontend