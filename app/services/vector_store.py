# ============================================================
# CHROMADB VECTOR STORE
# ============================================================
#
# Purpose:
#
# Store document embeddings and perform
# semantic similarity searches.
#
# In a RAG application:
#
# Documents
#      ↓
# Chunking
#      ↓
# Embeddings
#      ↓
# ChromaDB
#      ↓
# Semantic Search
#
# ChromaDB acts as the knowledge base
# for your Medical RAG Chatbot.
#
# ============================================================


# Import Chroma vector database integration
#
# LangChain wrapper around ChromaDB.
#
# Provides:
#
# - Store embeddings
# - Similarity search
# - Persistence
# - Metadata support
#
from pathlib import Path

from langchain_chroma import Chroma

# Import embedding model
#
# This model converts:
#
# Documents → Vectors
# Questions → Vectors
#
# Example:
#
# "What is diabetes?"
#
# →
#
# [0.123, -0.456, 0.789, ...]
#
from app.services.embeddings import embeddings

# Import directory path where ChromaDB
# stores its files.
#
# Example:
#
# CHROMA_DIR = "./chroma_db"
#
from app.core.config import CHROMA_DIR

# ============================================================
# CREATE / LOAD VECTOR DATABASE
# ============================================================
#
# If directory exists:
#
#     Load existing vector database
#
# If directory doesn't exist:
#
#     Create new vector database
#
# Chroma automatically handles both.
#
# ============================================================
_vector_db: Chroma | None = None


def get_vector_db(*, create: bool = False) -> Chroma:
    global _vector_db

    if _vector_db is not None:
        return _vector_db

    persist_dir = Path(CHROMA_DIR)
    if not create:
        sqlite_path = persist_dir / "chroma.sqlite3"
        if not persist_dir.exists() or not sqlite_path.exists():
            raise RuntimeError(
                "Vector store not initialized. Run POST /ingest or python -m scripts.ingest to load PDFs."
            )

    _vector_db = Chroma(
        persist_directory=CHROMA_DIR,
        embedding_function=embeddings,
    )
    return _vector_db
