# ============================================================
# RETRIEVER
# ============================================================
#
# Purpose:
#
# Retrieve relevant document chunks from
# the vector database using semantic search.
#
# This is the Retrieval part of RAG:
#
# RAG = Retrieval + Augmented + Generation
#
# Workflow:
#
# User Question
#       ↓
# Embedding Model
#       ↓
# Vector Search
#       ↓
# Relevant Chunks
#
# ============================================================


# Import vector database instance
#
# This object contains:
#
# - Embedded document chunks
# - Metadata
# - Similarity search capability
#
# Example:
#
# Chroma
# FAISS
# Qdrant
# Pinecone
#
from app.services.vector_store import get_vector_db


# ============================================================
# SEMANTIC SEARCH
# ============================================================
#
# Input:
#
# query:
#     User question
#
# k:
#     Number of chunks to retrieve
#
# Output:
#
# List of document texts
#
# Example:
#
# [
#   "Diabetes is a chronic disease...",
#   "Symptoms include thirst...",
#   "Treatment includes insulin..."
# ]
#
# ============================================================
def semantic_search(query, k=5):

    # ========================================================
    # VECTOR SIMILARITY SEARCH
    # ========================================================
    #
    # Internally:
    #
    # Step 1:
    # Convert query into embedding
    #
    # Query:
    # "What are symptoms of diabetes?"
    #
    # →
    #
    # [0.23, -0.45, 0.78, ...]
    #
    #
    # Step 2:
    # Compare query vector against all
    # document vectors stored in DB.
    #
    #
    # Step 3:
    # Calculate similarity score.
    #
    # Common metrics:
    #
    # - Cosine Similarity
    # - Dot Product
    # - Euclidean Distance
    #
    #
    # Step 4:
    # Return top-k matching documents.
    #
    # ========================================================
    docs = get_vector_db(create=False).similarity_search(query, k=k)


    # ========================================================
    # EXTRACT DOCUMENT TEXT
    # ========================================================
    #
    # similarity_search() returns
    # Document objects.
    #
    # Example:
    #
    # [
    #   Document(
    #      page_content="Diabetes..."
    #   ),
    #
    #   Document(
    #      page_content="Symptoms..."
    #   )
    # ]
    #
    # We only need the actual text.
    #
    # ========================================================
    return [d.page_content for d in docs]