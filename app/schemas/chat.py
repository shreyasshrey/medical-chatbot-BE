# Import BaseModel and Field from Pydantic
#
# BaseModel:
#     Used to define request and response schemas.
#
# Field:
#     Used to add validation rules, default values,
#     descriptions, examples, etc.
#
from pydantic import BaseModel, Field


# ============================================================
# CHAT REQUEST SCHEMA
# ============================================================
#
# This schema validates incoming requests
# sent to the /chat endpoint.
#
# Example Request:
#
# {
#     "question": "What are the symptoms of diabetes?",
#     "session_id": "session_123",
#     "stream": true
# }
#
# FastAPI automatically:
# 1. Validates request data
# 2. Converts JSON to Python object
# 3. Returns validation errors if invalid
#
# ============================================================
class ChatRequest(BaseModel):
    # --------------------------------------------------------
    # User Question
    #
    # Example:
    # "What is diabetes?"
    #
    # Field(...)
    #     ... means REQUIRED field
    #
    # min_length=1
    #     Prevents empty strings
    #
    # Valid:
    # "What is diabetes?"
    #
    # Invalid:
    # ""
    #
    # --------------------------------------------------------
    question: str = Field(..., min_length=1)
    # --------------------------------------------------------
    # Session ID
    #
    # Used to identify a conversation.
    #
    # Example:
    # "session_123"
    # "abc-def-456"
    #
    # Required field
    #
    # min_length=1
    # Prevents:
    # ""
    #
    # --------------------------------------------------------
    session_id: str = Field(..., min_length=1)
    # --------------------------------------------------------
    # Streaming Flag
    #
    # Determines whether the response should be:
    #
    # True  -> Stream token-by-token
    # False -> Return complete response
    #
    # Default:
    # True
    #
    # Example:
    #
    # {
    #     "stream": true
    # }
    #
    # If omitted:
    #
    # {
    #     "stream": true
    # }
    #
    # --------------------------------------------------------
    stream: bool = Field(True)
