# ============================================================
# QUESTION REWRITING MODULE
# ============================================================
#
# Purpose:
#
# Convert follow-up questions into standalone questions.
#
# This is a critical component in Conversational RAG.
#
# Why?
#
# Users often ask:
#
# User: What is diabetes?
# Bot: Diabetes is a chronic disease...
#
# User: What are its symptoms?
#
# The second question is incomplete because:
# "its" refers to diabetes.
#
# Vector databases cannot understand references like:
# - it
# - its
# - they
# - those
# - this disease
#
# Therefore we rewrite:
#
# "What are its symptoms?"
#
# into:
#
# "What are the symptoms of diabetes?"
#
# This significantly improves retrieval quality.
#
# ============================================================


# Import LLM calling utility
#
# This function sends prompts to the configured
# Hugging Face model and returns generated text.
from app.services.llm import call_llm


# ============================================================
# REWRITE FUNCTION
# ============================================================
#
# Inputs:
#
# question:
#     Current user question
#
# history:
#     Previous conversation history
#
# Output:
#
# Standalone question
#
# Example:
#
# Input:
#
# history:
# User: What is diabetes?
# Assistant: Diabetes is a chronic disease.
#
# question:
# What are its symptoms?
#
# Output:
#
# What are the symptoms of diabetes?
#
# ============================================================
def rewrite(question, history):

    # --------------------------------------------------------
    # Prompt Construction
    # --------------------------------------------------------
    #
    # We provide:
    #
    # 1. Conversation history
    # 2. Current user question
    #
    # Then ask the LLM to rewrite it
    # into a self-contained question.
    #
    # --------------------------------------------------------
    prompt = f"""
    Conversation:
    {history}

    Rewrite question into standalone medical question:
    {question}
    """

    # prompt = f"""
    # You are a query rewriting assistant.

    # Given the conversation history and the latest user question,
    # rewrite the question into a standalone medical question.

    # Rules:
    # - Preserve the original meaning.
    # - Resolve references such as:
    # - it
    # - they
    # - this condition
    # - that disease
    # - Do not answer the question.
    # - Return only the rewritten question.

    # Conversation:
    # {history}

    # Question:
    # {question}

    # Standalone Question:
    # """

    # --------------------------------------------------------
    # Send prompt to LLM
    # --------------------------------------------------------
    #
    # Example:
    #
    # Input:
    #
    # Conversation:
    # User: What is diabetes?
    #
    # Question:
    # What are its symptoms?
    #
    # Output:
    #
    # What are the symptoms of diabetes?
    #
    # --------------------------------------------------------
    return call_llm(prompt)