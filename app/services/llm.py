# Used to read environment variables
# Example:
# HF_TOKEN=xxxxxxxx
# HF_API_URL=https://router.huggingface.co/v1/chat/completions
import os

# HTTP client used to call Hugging Face APIs
import requests

# Import model configuration values
from app.core.config import (
    MAX_NEW_TOKENS,   # Maximum tokens model can generate
    MODEL_NAME,       # LLM model name
    TEMPERATURE       # Creativity/randomness parameter
)

# ============================================================
# HUGGING FACE API ENDPOINT
# ============================================================
#
# Reads HF_API_URL from environment variables.
#
# If not found, defaults to:
# https://router.huggingface.co/v1/chat/completions
#
# This endpoint supports OpenAI-compatible chat completion APIs.
#
# Example:
#
# HF_API_URL=https://router.huggingface.co/v1/chat/completions
#
# ============================================================
API_URL = os.getenv("HF_API_URL", "https://router.huggingface.co/v1/chat/completions")


# ============================================================
# CALL LLM FUNCTION
# ============================================================
#
# Purpose:
# Send prompt to Hugging Face hosted LLM
# and return generated response text.
#
# Input:
# prompt (string)
#
# Output:
# Generated answer (string)
#
# Example:
#
# answer = call_llm(
#     "What are symptoms of diabetes?"
# )
#
# ============================================================
def call_llm(prompt: str) -> str:

    # --------------------------------------------------------
    # Retrieve Hugging Face Access Token
    # --------------------------------------------------------
    #
    # Example:
    #
    # HF_TOKEN=hf_xxxxxxxxxxxxx
    #
    # Used for API authentication.
    #
    # --------------------------------------------------------
    hf_token = os.getenv("HF_TOKEN")
    
    # If token is missing, stop execution
    if not hf_token:
        raise RuntimeError("HF_TOKEN is not set")

    # --------------------------------------------------------
    # Validate Model Name
    # --------------------------------------------------------
    #
    # Example:
    #
    # MODEL_NAME=meta-llama/Llama-3.1-8B-Instruct
    #
    # --------------------------------------------------------
    if not MODEL_NAME:
        raise RuntimeError("MODEL_NAME is not set")

    # --------------------------------------------------------
    # HTTP Headers
    # --------------------------------------------------------
    #
    # Authorization:
    # Bearer token used by Hugging Face
    #
    # Content-Type:
    # JSON payload
    #
    # --------------------------------------------------------
    headers = {
        "Authorization": f"Bearer {hf_token}",
        "Content-Type": "application/json",
    }

    # ========================================================
    # CHAT COMPLETION API FORMAT
    # ========================================================
    #
    # Used by:
    # OpenAI-compatible Hugging Face Router
    #
    # Endpoint:
    # /v1/chat/completions
    #
    # ========================================================
    if "/v1/chat/completions" in API_URL:
        payload = {
            "model": MODEL_NAME,
            # Conversation messages in OpenAI format
            "messages": [{"role": "user", "content": prompt}],
            # Controls randomness of output. Higher = more random.
            "temperature": TEMPERATURE,
            # Maximum output length in tokens. Adjust based on expected response size.
            "max_tokens": MAX_NEW_TOKENS,
        }
        
    # ========================================================
    # LEGACY INFERENCE ENDPOINT FORMAT
    # ========================================================
    #
    # Some Hugging Face models expect:
    #
    # {
    #   "inputs": "...",
    #   "parameters": {...}
    # }
    #
    # ========================================================
    else:
        payload = {
            # Prompt text sent to the model for generation
            "inputs": prompt,
            "parameters": {
                # Creativity setting. Higher = more random output.
                "temperature": TEMPERATURE,
                # Maximum generated tokens. Adjust based on expected response size.
                "max_new_tokens": MAX_NEW_TOKENS,
                # Return only generated text
                # instead of prompt + answer. Some models return both by default.
                "return_full_text": False,
            },
        }

    # ========================================================
    # SEND REQUEST TO LLM
    # ========================================================
    #
    # timeout=60
    #
    # Wait at most 60 seconds
    # before failing.
    #
    # ========================================================
    response = requests.post(API_URL, headers=headers, json=payload, timeout=60)

    # ========================================================
    # HANDLE HTTP ERRORS
    # ========================================================
    #
    # Example:
    # 401 Unauthorized
    # 429 Rate Limit
    # 500 Server Error
    #
    # ========================================================
    if not response.ok:
        raise RuntimeError(f"LLM request failed ({response.status_code}): {response.text}")

    # ========================================================
    # PARSE JSON RESPONSE
    # ========================================================
    try:
        data = response.json()
    except ValueError:
        raise RuntimeError(f"LLM returned non-JSON response: {response.text}")

    # ========================================================
    # FORMAT 1:
    # OpenAI-Compatible Response
    # ========================================================
    #
    # Example:
    #
    # {
    #   "choices": [
    #     {
    #       "message": {
    #         "content": "Answer..."
    #       }
    #     }
    #   ]
    # }
    #
    # ========================================================
    if isinstance(data, dict) and "choices" in data:
        return data["choices"][0]["message"]["content"]
    
    # ========================================================
    # FORMAT 2:
    # Hugging Face List Response
    # ========================================================
    #
    # Example:
    #
    # [
    #   {
    #      "generated_text":"Answer..."
    #   }
    # ]
    #
    # ========================================================
    if isinstance(data, list) and data and isinstance(data[0], dict) and "generated_text" in data[0]:
        return data[0]["generated_text"]

    # ========================================================
    # FORMAT 3:
    # Hugging Face Dict Response
    # ========================================================
    #
    # Example:
    #
    # {
    #   "generated_text":"Answer..."
    # }
    #
    # ========================================================
    if isinstance(data, dict) and "generated_text" in data:
        return data["generated_text"]

    # ========================================================
    # FORMAT 4:
    # Hugging Face Error Response
    # ========================================================
    #
    # Example:
    #
    # {
    #   "error":"Model loading"
    # }
    #
    # ========================================================
    if isinstance(data, dict) and "error" in data:
        raise RuntimeError(f"LLM error: {data['error']}")

    # ========================================================
    # UNKNOWN RESPONSE FORMAT
    # ========================================================
    raise RuntimeError(f"Unexpected LLM response: {data}")