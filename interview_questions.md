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