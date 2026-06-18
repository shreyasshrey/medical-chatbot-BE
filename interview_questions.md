# database.py

Why use create_engine()?

create_engine() creates a connection pool and acts as the central object through which SQLAlchemy communicates with the database.

Why use sessionmaker()?

sessionmaker() creates database sessions that:

Execute queries
Insert records
Update records
Delete records
Manage transactions
Why pool_pre_ping=True?

MySQL may close idle connections. Before using a connection, SQLAlchemy checks whether it is still alive and reconnects if necessary.

Why pool_recycle=3600?

MySQL often drops connections after a timeout. Recycling every 3600 seconds (1 hour) prevents "MySQL server has gone away" errors.

Why create the database programmatically?

When deploying to a new environment:

No manual DB creation required
Application can initialize itself
Useful for Docker, Kubernetes, and CI/CD pipelines

# chat.py

Why use Pydantic Models?

Answer:
Pydantic models provide:

Automatic request validation
Type checking
Automatic JSON parsing
Auto-generated Swagger documentation
Cleaner and safer API code

Without ChatRequest, you'd manually validate every request field, making the code longer and more error-prone.

# embeddings.py

Why do we need embeddings in RAG?

Answer:
LLMs cannot efficiently search large document collections directly. Embeddings convert text into vectors that capture semantic meaning. By comparing vector similarity, we can retrieve the most relevant document chunks for a user query and provide them as context to the LLM, enabling accurate and context-aware responses.

# llm.py

Why support multiple response formats?

Different Hugging Face endpoints return different JSON structures

# memory.py

Why separate memory into two tables?
chat_sessions

Stores:

Session metadata
Created date
Updated date
chat_messages

Stores:

Individual messages
User questions
Assistant responses
Benefits
One-to-Many Relationship
Faster session listing
Easy chat deletion
Better scalability
Sidebar conversation support
Supports millions of messages efficiently

This memory layer is what makes my chatbot conversational, because previous messages can be retrieved via get_history() and injected into the RAG context before calling the LLM.

# query_rewriter.py

Why rewrite the question before retrieval?

Answer:

In conversational systems, users often ask follow-up questions containing pronouns or references to earlier messages. Vector databases perform retrieval based on the current query and do not inherently understand conversational context. Question rewriting converts context-dependent queries into standalone queries, improving embedding quality and retrieval accuracy. This leads to better context selection and more accurate RAG responses.

# reranker.py

Why use a CrossEncoder after semantic search?

Answer:

Embedding-based retrieval (Bi-Encoder) is fast and scalable but may not rank documents optimally. A CrossEncoder evaluates the query and document together, capturing deeper semantic relationships and producing more accurate relevance scores. Therefore, a common RAG architecture retrieves the top-k documents using embeddings and then reranks them with a CrossEncoder before sending context to the LLM.

# retriever.py

What is the role of semantic search in a RAG system?

Answer:

Semantic search retrieves document chunks based on meaning rather than exact keyword matches. It converts both user queries and documents into vector embeddings and uses similarity measures such as cosine similarity to identify the most relevant content. This allows RAG systems to retrieve context even when the wording differs, improving answer quality and retrieval accuracy.

# streaming.py

What is the difference between simulated streaming and true streaming?

Answer:

Simulated streaming generates the complete response first and then sends it incrementally to the client, usually word-by-word or chunk-by-chunk. True streaming sends tokens to the client as the LLM generates them, reducing perceived latency and improving user experience. Production-grade AI applications typically use true streaming through APIs that support token-level generation streams.

# vector_store.py

Why use ChromaDB in a RAG application?

Answer:

ChromaDB is a vector database used to store document embeddings and perform semantic similarity searches. When a user asks a question, the query is converted into an embedding and compared against stored document vectors. The most relevant chunks are retrieved and supplied as context to the LLM, enabling Retrieval-Augmented Generation (RAG). ChromaDB also supports persistence, metadata storage, and efficient nearest-neighbor search.

what if i delete the medical-chatbot-BE\data\chroma_db\chroma.sqlite3 the application will work normally
if user asks the question?

Answer:
Yes, the API will still run, but your RAG “knowledge base” will be effectively gone.

- Your vector store is loaded here: vector_store.py using Chroma(persist_directory=CHROMA_DIR) . If data/chroma_db/chroma.sqlite3 is deleted, Chroma typically recreates an empty persistent store at that path.
- Then retrieval returns no chunks: semantic_search → [] , so build_context produces context = "" .
What you’ll see when a user asks a question

- stream=false (Swagger-friendly JSON): it will usually respond with the out-of-context fallback and suggested_questions: [] because the context is empty ( routes.py ).
- stream=true (SSE): the prompt in streaming mode does not enforce “use only context” strictly ( routes.py ), so the LLM may still answer from general knowledge (hallucination risk), but it won’t be grounded in your PDFs.

If I deleted only chroma.sqlite3 but left other files in data\chroma_db , and you hit weird errors, delete the whole folder contents and re-run ingestion (clean rebuild).


If you dropped the schema/database or the tables in MySQL Workbench, anything in the backend that reads/writes chat history will fail until you restart (and the data is gone).

What each API will do now

- GET /health → still returns {"status":"ok"} (no DB access) ( main.py ).
- POST /ingest → still works (it only loads PDFs into Chroma, not MySQL).
- GET /chat/sessions → will error (depends on MySQL via list_sessions() in memory.py ).
- GET /chat/history/{session_id} → will error (depends on MySQL via get_history() ).
- DELETE /chat/history/{session_id} → will error (depends on MySQL via clear_memory() ).
- POST /chat → will error because build_context() calls get_history() first, and later save_message() writes to DB ( rag.py , routes.py ).
How to recover

- Restart the backend. On startup it runs ensure_database_exists() and Base.metadata.create_all(...) ( main.py ), which recreates the database/tables if missing.
- After restart, APIs will work again, but the previous chat history is permanently deleted.


# Medical RAG Chatbot - Interview Questions & Answers

## Table of Contents

1. Project Overview
2. Architecture & System Design
3. FastAPI Questions
4. API Layer (`routes.py`)
5. MySQL & SQLAlchemy
6. Chat Memory (`memory.py`)
7. Query Rewriting (`query_rewriter.py`)
8. Embeddings (`embeddings.py`)
9. ChromaDB (`vector_store.py`)
10. Semantic Search (`retriever.py`)
11. RAG Pipeline (`rag.py`)
12. Reranking (`reranker.py`)
13. LLM Integration (`llm.py`)
14. Streaming (`streaming.py`)
15. Prompt Engineering
16. Production Readiness
17. Scalability
18. Security
19. System Design
20. Senior-Level Questions

---

# 1. Project Overview Questions

## Q1. Explain your Medical RAG Chatbot project.

### Answer

My project is a Conversational Medical RAG (Retrieval-Augmented Generation) Chatbot built using FastAPI, MySQL, ChromaDB, Hugging Face Embeddings, Hugging Face LLMs, Query Rewriting, Cross-Encoder Reranking, and Server-Sent Events (SSE) streaming.

The application allows users to ask questions related to uploaded medical documents. Instead of relying solely on an LLM's training knowledge, the chatbot retrieves relevant information from a vector database and uses that context to generate accurate responses.

Main components include:

* FastAPI Backend
* ChromaDB Vector Store
* HuggingFace Embeddings
* Query Rewriting
* Semantic Search
* Cross-Encoder Reranking
* MySQL Chat Memory
* HuggingFace LLM
* SSE Streaming

---

## Q2. Why did you choose RAG instead of fine-tuning?

### Answer

Fine-tuning requires retraining a model whenever new documents are added.

RAG offers:

* Dynamic knowledge updates
* Lower cost
* Better explainability
* Reduced hallucinations
* No retraining required

New documents can simply be embedded and stored in the vector database.

---

## Q3. What problem does RAG solve?

### Answer

Large Language Models have static knowledge and cannot access newly uploaded documents.

RAG solves this by:

1. Retrieving relevant information from external documents.
2. Injecting that information into the prompt.
3. Allowing the LLM to answer using current knowledge.

---

## Q4. What are the main components of your application?

### Answer

1. Frontend (React)
2. FastAPI Backend
3. MySQL Memory Layer
4. Query Rewriter
5. Embedding Model
6. ChromaDB
7. Semantic Retriever
8. Reranker
9. LLM
10. Streaming Layer

---

# 2. Architecture Questions

## Q5. Explain the end-to-end architecture.

### Answer

Flow:

User Question
↓
FastAPI Route
↓
Load Chat Memory
↓
Rewrite Question
↓
Generate Embedding
↓
Semantic Search
↓
Rerank Results
↓
Build Context
↓
Create Prompt
↓
LLM
↓
Stream Response
↓
Save Conversation

---

## Q6. Why do you need both MySQL and ChromaDB?

### Answer

MySQL stores conversational memory:

* Sessions
* User messages
* Assistant messages

ChromaDB stores knowledge embeddings:

* Medical document chunks
* Vector representations

MySQL handles conversation history while ChromaDB handles knowledge retrieval.

---

## Q7. How do you prevent hallucinations?

### Answer

Several techniques are used:

1. Retrieval-Augmented Generation
2. Query Rewriting
3. Cross-Encoder Reranking
4. Context-only Prompting
5. Out-of-context Detection
6. Structured JSON Output

The model is instructed to answer only from retrieved context.

---

# 3. FastAPI Questions

## Q8. Why did you choose FastAPI?

### Answer

Advantages:

* High performance
* Async support
* Automatic OpenAPI documentation
* Built-in validation using Pydantic
* Easy integration with AI services

---

## Q9. What is the purpose of lifespan()?

### Answer

The lifespan function runs startup and shutdown tasks.

In my project it:

* Creates the database if missing
* Creates database tables
* Initializes required resources

---

## Q10. Why use APIRouter?

### Answer

APIRouter helps organize endpoints into separate modules.

Benefits:

* Cleaner code
* Better maintainability
* Easier scaling

---

# 4. API Layer (routes.py)

## Q11. Walk me through the /chat endpoint.

### Answer

Steps:

1. Receive user question.
2. Get session id.
3. Load memory.
4. Rewrite question.
5. Retrieve relevant documents.
6. Rerank documents.
7. Build final context.
8. Create prompt.
9. Call LLM.
10. Save conversation.
11. Return answer.

---

## Q12. Why do you return suggested questions?

### Answer

Suggested questions improve user engagement.

They:

* Guide exploration
* Increase conversation depth
* Improve UX

The LLM generates follow-up questions from the retrieved context.

---

# 5. MySQL & SQLAlchemy Questions

## Q13. Why use SQLAlchemy?

### Answer

SQLAlchemy provides ORM capabilities.

Benefits:

* Database abstraction
* Easier CRUD operations
* Better maintainability
* Reduced SQL boilerplate

---

## Q14. What is ORM?

### Answer

ORM stands for Object Relational Mapping.

It maps database tables to Python classes.

Example:

ChatSession table ↔ ChatSession class

ChatMessage table ↔ ChatMessage class

---

## Q15. Difference between flush() and commit()?

### Answer

flush()

* Sends changes to database
* Does not permanently save

commit()

* Permanently saves transaction

In save_message() flush() is used to create the session before inserting dependent messages.

---

# 6. Chat Memory Questions

## Q16. Why maintain chat memory?

### Answer

Without memory:

User: What is diabetes?
User: What are its symptoms?

The second question lacks context.

Memory allows the system to understand conversational references.

---

## Q17. How is chat history stored?

### Answer

Using two tables:

chat_sessions

Stores:

* session_id
* created_at
* updated_at

chat_messages

Stores:

* message id
* session id
* role
* content
* timestamp

---

# 7. Query Rewriting Questions

## Q18. What is query rewriting?

### Answer

Query rewriting converts follow-up questions into standalone questions.

Example:

Original:

"What are its symptoms?"

Rewritten:

"What are the symptoms of diabetes?"

---

## Q19. Why is query rewriting important?

### Answer

Vector databases work best with complete questions.

Rewriting improves retrieval quality and retrieval accuracy.

---

# 8. Embeddings Questions

## Q20. What are embeddings?

### Answer

Embeddings are numerical vector representations of text.

Example:

"What is diabetes?"

↓

[0.12, -0.44, 0.89, ...]

Embeddings allow semantic similarity comparisons.

---

## Q21. Why use the same embedding model for indexing and retrieval?

### Answer

Both document embeddings and query embeddings must exist in the same vector space.

Using different models can produce incompatible vectors and poor retrieval.

---

# 9. ChromaDB Questions

## Q22. What is ChromaDB?

### Answer

ChromaDB is a vector database used to store document embeddings and perform similarity search.

---

## Q23. What is persistence in ChromaDB?

### Answer

Persistence stores vectors on disk.

Benefits:

* Survive application restarts
* Faster startup
* No need to regenerate embeddings

---

# 10. Semantic Search Questions

## Q24. What is semantic search?

### Answer

Semantic search retrieves results based on meaning rather than exact keywords.

Example:

Query:

"What are signs of diabetes?"

Document:

"Symptoms of diabetes include..."

Semantic search recognizes that signs and symptoms are related.

---

## Q25. Difference between keyword search and semantic search?

### Answer

Keyword Search:

Matches exact words.

Semantic Search:

Matches meaning using embeddings.

Semantic search generally provides better retrieval quality in RAG systems.

---

# 11. Reranking Questions

## Q26. Why use reranking?

### Answer

Vector search retrieves approximate matches.

Reranking improves ordering of retrieved documents and increases context quality.

---

## Q27. What is a CrossEncoder?

### Answer

A CrossEncoder evaluates:

(Query, Document)

together and produces a relevance score.

It is more accurate than embedding similarity but slower.

---

# 12. LLM Questions

## Q28. What is temperature?

### Answer

Temperature controls randomness.

Low temperature:

* More deterministic
* More consistent

High temperature:

* More creative
* Less predictable

Medical applications generally use lower temperatures.

---

## Q29. What is max_tokens?

### Answer

Defines the maximum number of tokens generated by the model.

It controls response length and inference cost.

---

# 13. Streaming Questions

## Q30. What is SSE?

### Answer

SSE stands for Server-Sent Events.

It enables servers to push updates to clients over HTTP.

Used for streaming AI responses.

---

## Q31. Is your implementation true streaming?

### Answer

No.

Current implementation:

1. Generate full response.
2. Split response into words.
3. Stream words one-by-one.

This is simulated streaming.

True streaming would send tokens as the model generates them.

---

# 14. Senior-Level Questions

## Q32. How would you scale this application?

### Answer

1. Move ChromaDB to a distributed vector database.
2. Add Redis caching.
3. Deploy FastAPI behind a load balancer.
4. Use Kubernetes.
5. Implement asynchronous workers.
6. Use managed databases.

---

## Q33. How would you evaluate the RAG system?

### Answer

Metrics:

* Retrieval Precision
* Recall@K
* MRR
* Faithfulness
* Groundedness
* Answer Relevance
* Hallucination Rate

---

## Q34. What improvements would you make for production?

### Answer

1. Hybrid Search (BM25 + Vector Search)
2. Real Token Streaming
3. LangSmith Observability
4. Prompt Versioning
5. Redis Cache
6. Authentication & Authorization
7. Evaluation Pipeline
8. Citation Generation
9. Multi-document Support
10. Guardrails and Safety Checks

---

# End of Interview Guide

This document covers the core concepts of:

* FastAPI
* SQLAlchemy
* MySQL
* ChromaDB
* Embeddings
* Semantic Search
* Query Rewriting
* RAG
* CrossEncoder Reranking
* Hugging Face LLMs
* Streaming
* System Design

and is suitable for GenAI Developer, AI Engineer, LLM Engineer, RAG Engineer, and Full Stack AI Developer interviews.
