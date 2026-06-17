# ============================================================
# RAG PIPELINE
# ============================================================
#
# Purpose:
#
# Build the final context that will be sent to the LLM.
#
# This pipeline combines:
#
# 1. Conversation Memory
# 2. Query Rewriting
# 3. Semantic Search
# 4. Reranking
# 5. Context Construction
#
# Output:
#
# - standalone question
# - retrieved context
# - chat history
#
# This is the core orchestration layer of the RAG system.
#
# ============================================================


# ============================================================
# IMPORTS
# ============================================================

# Semantic retrieval from vector database
from app.services.retriever import semantic_search
# Cross-encoder reranking
from app.services.reranker import rerank
# Follow-up question → standalone question
from app.services.query_rewriter import rewrite
# Chat memory retrieval
from app.services.memory import get_history


# ============================================================
# BUILD CONTEXT
# ============================================================
#
# Input:
#
# question:
#     Latest user question
#
# session_id:
#     Chat session identifier
#
# Output:
#
# standalone_q:
#     Rewritten standalone question
#
# context:
#     Top retrieved document chunks
#
# history:
#     Previous conversation history
#
# ============================================================
def build_context(question, session_id):

    # ========================================================
    # STEP 1: LOAD CHAT MEMORY
    # ========================================================
    #
    # Retrieves all previous messages
    # belonging to this session.
    #
    # Example:
    #
    # [
    #   {
    #     "role":"user",
    #     "content":"What is diabetes?"
    #   },
    #   {
    #     "role":"assistant",
    #     "content":"Diabetes is..."
    #   }
    # ]
    #
    # ========================================================
    history = get_history(session_id)

    # ========================================================
    # STEP 2: QUESTION REWRITING
    # ========================================================
    #
    # Converts follow-up questions
    # into standalone questions.
    #
    # Example:
    #
    # Conversation:
    # User: What is diabetes?
    #
    # Question:
    # What are its symptoms?
    #
    # Rewritten:
    # What are the symptoms of diabetes?
    #
    # This improves retrieval quality.
    #
    # ========================================================
    standalone_q = rewrite(question, history)

    # ========================================================
    # STEP 3: SEMANTIC SEARCH
    # ========================================================
    #
    # Generate embedding for:
    #
    # standalone_q
    #
    # Search vector database
    # for most relevant chunks.
    #
    # k=10
    #
    # Retrieve top 10 candidate chunks.
    #
    # Example:
    #
    # [
    #   "Diabetes symptoms include...",
    #   "Type 2 diabetes causes...",
    #   ...
    # ]
    #
    # ========================================================
    docs = semantic_search(standalone_q, k=10)

    # ========================================================
    # STEP 4: RERANK RESULTS
    # ========================================================
    #
    # Semantic search retrieves
    # approximately relevant documents.
    #
    # Reranker evaluates:
    #
    # Question + Document
    #
    # and produces better relevance scores.
    #
    # Example:
    #
    # Before:
    #
    # 1. Diabetes causes
    # 2. Diabetes symptoms
    # 3. Diabetes treatment
    #
    # After reranking:
    #
    # 1. Diabetes symptoms
    # 2. Diabetes causes
    # 3. Diabetes treatment
    #
    # ========================================================
    docs = rerank(standalone_q, docs)

    # ========================================================
    # STEP 5: BUILD FINAL CONTEXT
    # ========================================================
    #
    # Keep only top 5 documents.
    #
    # Join them into one context string.
    #
    # Example:
    #
    # Chunk 1
    # Chunk 2
    # Chunk 3
    # Chunk 4
    # Chunk 5
    #
    # ========================================================
    context = "\n".join(docs[:5])


    # ========================================================
    # RETURN RESULTS
    # ========================================================
    #
    # standalone_q:
    #     Rewritten question
    #
    # context:
    #     Retrieved knowledge
    #
    # history:
    #     Chat memory
    #
    # ========================================================
    return standalone_q, context, history