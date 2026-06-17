# ============================================================
# CROSS-ENCODER RERANKER
# ============================================================
#
# Purpose:
#
# Improve retrieval quality after semantic search.
#
# Semantic Search:
# ----------------
# Retrieves top-k documents based on vector similarity.
#
# Problem:
#
# The most similar embedding is not always
# the most relevant answer.
#
# Example:
#
# Query:
# "What are symptoms of diabetes?"
#
# Retrieved:
#
# 1. Diabetes treatment options
# 2. Diabetes symptoms
# 3. Diabetes causes
#
# Semantic search may not perfectly rank them.
#
# Cross-encoder reranking fixes this.
#
# ============================================================


# Import CrossEncoder model
#
# Unlike embedding models,
# CrossEncoder evaluates:
#
# Query + Document
#
# together.
#
# Example:
#
# Query:
# "What are symptoms of diabetes?"
#
# Document:
# "Symptoms include thirst..."
#
# Output:
#
# Relevance Score:
# 0.98
#
from sentence_transformers import CrossEncoder

# ============================================================
# LOAD RERANKER MODEL
# ============================================================
#
# BAAI/bge-reranker-large
#
# One of the best open-source rerankers.
#
# Purpose:
#
# Given:
# (query, document)
#
# Predict:
# relevance score
#
# Example:
#
# Query:
# "What are symptoms of diabetes?"
#
# Doc:
# "Symptoms include fatigue..."
#
# Score:
# 0.99
#
# ============================================================
reranker = CrossEncoder("BAAI/bge-reranker-large")


# ============================================================
# RERANK FUNCTION
# ============================================================
#
# Input:
#
# query:
#     User question
#
# docs:
#     Documents retrieved by semantic search
#
# Output:
#
# Same documents reordered by relevance.
#
# ============================================================
def rerank(query, docs):

    # ========================================================
    # CREATE QUERY-DOCUMENT PAIRS
    # ========================================================
    #
    # CrossEncoder requires:
    #
    # [
    #   (query, doc1),
    #   (query, doc2),
    #   (query, doc3)
    # ]
    #
    # Example:
    #
    # [
    #   (
    #     "What are symptoms of diabetes?",
    #     "Symptoms include fatigue..."
    #   ),
    #
    #   (
    #     "What are symptoms of diabetes?",
    #     "Treatment options include..."
    #   )
    # ]
    #
    # ========================================================
    pairs = [(query, d) for d in docs]

    # ========================================================
    # PREDICT RELEVANCE SCORES
    # ========================================================
    #
    # Example Output:
    #
    # [0.98, 0.35, 0.72]
    #
    # Meaning:
    #
    # Doc1 = highly relevant
    # Doc2 = less relevant
    # Doc3 = moderately relevant
    #
    # ========================================================
    scores = reranker.predict(pairs)

    # ========================================================
    # COMBINE DOCS + SCORES
    # ========================================================
    #
    # zip(docs, scores)
    #
    # Example:
    #
    # [
    #   ("Symptoms include...", 0.98),
    #   ("Treatment options...", 0.35),
    #   ("Causes include...", 0.72)
    # ]
    #
    # ========================================================
    ranked = sorted(
        zip(docs, scores),
        key=lambda x: x[1],
        reverse=True
    )

    # ========================================================
    # RETURN ONLY DOCUMENTS
    # ========================================================
    #
    # Remove scores and keep ranking.
    #
    # Example:
    #
    # [
    #   "Symptoms include...",
    #   "Causes include...",
    #   "Treatment options..."
    # ]
    #
    # ========================================================
    return [doc for doc, _ in ranked]