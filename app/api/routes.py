# Import JSON module for parsing LLM responses
import json
# Import Regular Expression module for extracting JSON from text
import re

# FastAPI components for defining API routes and handling HTTP exceptions
from fastapi import APIRouter, HTTPException

# Server-Sent Events (SSE) support for streaming responses
from sse_starlette.sse import EventSourceResponse

# Request schema (Pydantic model) for validating incoming chat requests
from app.schemas.chat import ChatRequest
# Service that calls the LLM with a given prompt and returns the response
from app.services.llm import call_llm
# Memory service functions for managing chat history and sessions
from app.services.memory import clear_memory, get_history, list_sessions, save_message
# RAG service used to build context from documents + chat history
from app.services.rag import build_context
# Streaming service used for token-by-token response generation
from app.services.streaming import stream_response

from scripts.ingest import ingest_pdfs

# Create FastAPI router instance
router = APIRouter()


# ============================================================
# GET ALL CHAT SESSIONS
# ============================================================
@router.get("/chat/sessions")
def get_sessions():
    """
    Returns all available chat sessions.

    Example:
    [
        session_1,
        session_2,
        session_3
    ]
    """
    return {"sessions": list_sessions()}


# ============================================================
# GET CHAT HISTORY
# ============================================================
@router.get("/chat/history/{session_id}")
def chat_history(session_id: str):
    """
    Fetch complete conversation history
    for a given session.
    """
    # Retrieve messages from database based on session_id
    messages = get_history(session_id)
    # If no messages exist for the session, return 404 error
    if not messages:
        raise HTTPException(status_code=404, detail="Session not found or has no messages.")
    # Return history
    return {"session_id": session_id, "messages": messages}


# ============================================================
# DELETE CHAT HISTORY
# ============================================================
@router.delete("/chat/history/{session_id}")
def delete_chat_history(session_id: str):
    """
    Delete all messages associated with a session.
    """
    # Remove memory from database based on session_id
    clear_memory(session_id)
    return {"session_id": session_id, "deleted": True}


@router.post("/ingest")
def ingest():
    print("POST /ingest called", flush=True)
    try:
        result = ingest_pdfs()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    print("POST /ingest completed", flush=True)
    return result


# ============================================================
# MAIN CHAT ENDPOINT
# ============================================================
@router.post("/chat")
def chat(request: ChatRequest):

    # User question and session ID from request body
    question = request.question
    session_id = request.session_id

    # --------------------------------------------------------
    # Build RAG Context
    # --------------------------------------------------------
    #
    # standalone_q:
    #     Rewritten question with conversational references removed
    #
    # context:
    #     Relevant chunks retrieved from vector DB
    #
    # history:
    #     Previous conversation history
    #
    # --------------------------------------------------------
    try:
        standalone_q, context, history = build_context(
            question,
            session_id,
        )
    except RuntimeError as e:
        msg = str(e)
        if "Vector store not initialized" in msg:
            raise HTTPException(status_code=400, detail=msg)
        raise

    # --------------------------------------------------------
    # Prompt for streaming mode
    # --------------------------------------------------------
    prompt = f"""
        You are a medical assistant.

        Context:
        {context}

        Question:
        {standalone_q}

        Answer:
        """

    # ========================================================
    # STREAMING RESPONSE FLOW
    # ========================================================
    if request.stream:

        # SSE Generator
        def event_generator():

            # Accumulate full answer
            answer = ""

            # Stream token-by-token response from LLM
            for token in stream_response(prompt):

                # Build final answer
                answer += token

                # Send token to frontend
                yield {"event": "token", "data": token}

            # Save user message
            save_message(session_id, "user", question)
            # Save assistant response
            save_message(session_id, "assistant", answer)

        # Return Server Sent Events stream
        return EventSourceResponse(event_generator())

    # ========================================================
    # NON-STREAMING FLOW
    # ========================================================

    # Standard response if answer doesn't exist in context
    OUT_OF_CONTEXT_ANSWER = "I can only answer questions related to medical topics and the uploaded documents."

    # --------------------------------------------------------
    # Structured JSON Prompt
    # --------------------------------------------------------
    #
    # Force model to:
    # 1. Use only retrieved context
    # 2. Return JSON
    # 3. Generate follow-up questions
    #
    # --------------------------------------------------------
    structured_prompt = f"""
        You are a medical assistant.

        Use ONLY the provided context. Do NOT use any external or general knowledge.

        If the answer is not found in the context:
        - Set answer to: "{OUT_OF_CONTEXT_ANSWER}"
        - Set suggested_questions to: []

        If the answer IS found in the context:
        - Set answer to the relevant answer
        - Set suggested_questions to an array of 3 short follow-up questions based on the context

        Context:
        {context}

        Question:
        {standalone_q}

        Return a JSON object with keys:
        - answer: string
        - suggested_questions: array (3 questions if in context, empty [] if not)

        Return JSON only. No markdown. No extra text.
        """

    # --------------------------------------------------------
    # Call LLM
    # --------------------------------------------------------
    raw = call_llm(structured_prompt).strip()

    # Default values
    answer = raw
    suggested_questions: list[str] = []

    # ========================================================
    # Helper Function
    # ========================================================
    def _coerce(data: object) -> tuple[str, list[str]]:
        
        """
        Safely extract:
            answer
            suggested_questions
        from LLM response.
        """

        # If response isn't JSON object, return raw text and empty suggestions
        if not isinstance(data, dict):
            return raw, []

        # Extract answer and suggested questions with safety checks
        a = str(data.get("answer", "")).strip()
        sq = data.get("suggested_questions", [])


        out_sq: list[str] = []
        
        # Validate questions list
        if isinstance(sq, list):
            for item in sq:
                s = str(item).strip()
                if s:
                    out_sq.append(s)

        # Return parsed values
        return (a or raw), out_sq


    # ========================================================
    # Parse JSON Response
    # ========================================================
    try:
        # Direct JSON parsing
        answer, suggested_questions = _coerce(json.loads(raw))
    except json.JSONDecodeError:
        # Sometimes LLM adds extra text around JSON
        m = re.search(r"\{[\s\S]*\}", raw)
        if m:
            try:
                answer, suggested_questions = _coerce(json.loads(m.group(0)))
            except json.JSONDecodeError:
                pass

    # ========================================================
    # Safety Check
    # ========================================================
    #
    # If answer indicates out-of-context,
    # remove suggested questions.
    #
    # ========================================================
    if OUT_OF_CONTEXT_ANSWER.lower() in answer.lower() or "i can only answer" in answer.lower():
        suggested_questions = []

    # ========================================================
    # Save Conversation
    # ========================================================
    save_message(session_id, "user", question)
    save_message(session_id, "assistant", answer)

    # ========================================================
    # Final API Response
    # ========================================================
    return {
        "answer": answer,
        "suggested_questions": suggested_questions,
    }