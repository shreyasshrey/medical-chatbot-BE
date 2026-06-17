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
vector_db = Chroma(
    # Directory where vectors are persisted
    #
    # Example:
    #
    # ./chroma_db
    #
    persist_directory=CHROMA_DIR,
    # Embedding model used for:
    #
    # - Storing documents
    # - Searching documents
    #
    # IMPORTANT:
    #
    # The same embedding model must be used
    # for indexing and querying.
    #
    embedding_function=embeddings
)