# ============================================================
# STREAMING RESPONSE MODULE
# ============================================================
#
# Purpose:
#
# Simulate token streaming from the LLM.
#
# Current Implementation:
#
# 1. Get complete response from LLM
# 2. Split response into words
# 3. Yield words one-by-one
# 4. Add small delay
#
# This creates a typing effect similar to:
#
# ChatGPT
# Gemini
# Claude
#
# IMPORTANT:
#
# This is NOT true LLM streaming.
#
# The entire response is generated first,
# then streamed artificially.
#
# ============================================================
import time

# Import LLM utility
#
# This function sends the prompt to
# Hugging Face and returns the full response.
#
from app.services.llm import call_llm


# ============================================================
# STREAM RESPONSE FUNCTION
# ============================================================
#
# Input:
#
# prompt:
#     Final prompt sent to LLM
#
# Output:
#
# Generator yielding chunks of text
#
# Example:
#
# "Diabetes is a chronic disease."
#
# becomes:
#
# "Diabetes "
# "is "
# "a "
# "chronic "
# "disease. "
#
# ============================================================
def stream_response(prompt: str):

    # ========================================================
    # STEP 1: CALL LLM
    # ========================================================
    #
    # Generate complete response.
    #
    # Example:
    #
    # response =
    # "Diabetes is a chronic disease."
    #
    # ========================================================
    response = call_llm(prompt)
    
    # ========================================================
    # DEBUG LOG
    # ========================================================
    #
    # Print generated response to server console.
    #
    # flush=True ensures immediate output.
    #
    # Useful during development.
    #
    # Example:
    #
    # Full response received from LLM,
    # now streaming word-by-word...
    #
    # ========================================================
    print("Full response received from LLM, now streaming word-by-word...", response, flush=True)

    # ========================================================
    # STEP 2: SPLIT INTO WORDS
    # ========================================================
    #
    # response.split()
    #
    # Example:
    #
    # "Diabetes is a chronic disease."
    #
    # becomes:
    #
    # [
    #   "Diabetes",
    #   "is",
    #   "a",
    #   "chronic",
    #   "disease."
    # ]
    #
    # ========================================================
    for word in response.split():

        # ====================================================
        # STEP 3: YIELD WORD
        # ====================================================
        #
        # Generator sends one word
        # back to FastAPI SSE endpoint.
        #
        # Example:
        #
        # yield "Diabetes "
        # yield "is "
        # yield "a "
        #
        # ====================================================
        yield word + " "

        # ====================================================
        # STEP 4: DELAY
        # ====================================================
        #
        # Creates typing effect.
        #
        # 0.03 seconds
        # = 30 milliseconds
        #
        # Makes UI feel like
        # real-time generation.
        #
        # ====================================================
        time.sleep(0.03)