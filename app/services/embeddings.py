# ============================================================
# HUGGINGFACE EMBEDDINGS
# ============================================================
#
# Embeddings are numerical vector representations of text.
#
# They convert text into high-dimensional numbers
# that capture semantic meaning.
#
# Example:
#
# "What is diabetes?"
#        ↓
# [0.123, -0.456, 0.789, ...]
#
# Similar texts produce similar vectors.
#
# Example:
#
# "What is diabetes?"
# "Explain diabetes"
#
# These vectors will be close together
# in vector space.
#
# Embeddings are the foundation of:
# - Semantic Search
# - RAG Applications
# - Similarity Search
# - Vector Databases
#
# ============================================================


# Import HuggingFace embedding wrapper from LangChain
#
# This class provides an interface to generate embeddings
# using HuggingFace models.
from langchain_huggingface import HuggingFaceEmbeddings

# Import embedding model name from configuration
#
# Example:
#
# EMBEDDING_MODEL =
# "sentence-transformers/all-MiniLM-L6-v2"
#
# or
#
# "BAAI/bge-m3"
#
from app.core.config import EMBEDDING_MODEL

# ============================================================
# CREATE EMBEDDING MODEL
# ============================================================
#
# Loads the HuggingFace embedding model into memory.
#
# Once loaded, it can convert:
#
# Documents → Vectors
# Questions → Vectors
#
# These vectors are later stored and searched
# inside a vector database.
#
# ============================================================
embeddings = HuggingFaceEmbeddings(
    # Name of HuggingFace model to load
    model_name=EMBEDDING_MODEL
)