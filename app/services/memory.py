# Used for updating session timestamps
from datetime import datetime

# Database session factory
from app.db.database import SessionLocal
# ORM Models
from app.db.models import ChatMessage, ChatSession


# ============================================================
# GET CHAT HISTORY
# ============================================================
#
# Purpose:
# Retrieve all messages belonging to a session.
#
# Input:
# session_id
#
# Output:
# [
#   {
#     "role": "user",
#     "content": "What is diabetes?"
#   },
#   {
#     "role": "assistant",
#     "content": "Diabetes is..."
#   }
# ]
#
# Used by:
# - Conversational Memory
# - Context Building
# - Chat History Screen
#
# ============================================================
def get_history(session_id: str) -> list[dict]:
    """Return all messages for a session ordered by creation time."""
    
    # Create database session
    #
    # Automatically closes when block exits
    #
    with SessionLocal() as db:
        # Query chat_messages table
        messages = (
            db.query(ChatMessage)
            .filter(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.created_at)
            # Execute query
            .all()
        )
        # Convert ORM objects to dictionaries
        return [{"role": m.role, "content": m.content} for m in messages]


# ============================================================
# SAVE MESSAGE
# ============================================================
#
# Purpose:
# Save user or assistant message.
#
# Also ensures:
# - Session exists
# - Session updated timestamp is refreshed
#
# Example:
#
# save_message(
#     "session_001",
#     "user",
#     "What is diabetes?"
# )
#
# ============================================================
def save_message(session_id: str, role: str, content: str) -> None:
    """Persist a single message and ensure the parent session exists."""
    with SessionLocal() as db:
        
        # ----------------------------------------------------
        # Find existing session
        #
        # Equivalent SQL:
        #
        # SELECT *
        # FROM chat_sessions
        # WHERE id = session_id
        #
        # ----------------------------------------------------
        session = db.get(ChatSession, session_id)
        
        # ----------------------------------------------------
        # Session doesn't exist
        #
        # Create new chat session
        # ----------------------------------------------------
        if session is None:
            session = ChatSession(id=session_id)
            db.add(session)
            # ------------------------------------------------
            # Flush writes pending changes
            # without committing.
            #
            # Ensures session row exists
            # before message insert.
            #
            # Needed because:
            #
            # ChatMessage.session_id
            # references ChatSession.id
            #
            # via Foreign Key.
            # ------------------------------------------------
            db.flush()  # write the session row before the FK-dependent message
            
        # ----------------------------------------------------
        # Existing session found
        #
        # Update activity timestamp.
        # ----------------------------------------------------
        else:
            session.updated_at = datetime.utcnow()

        # ----------------------------------------------------
        # Save chat message
        #
        # INSERT INTO chat_messages
        # ----------------------------------------------------
        db.add(ChatMessage(session_id=session_id, role=role, content=content))
        # ----------------------------------------------------
        # Commit transaction
        #
        # Saves:
        # - Session
        # - Message
        #
        # ----------------------------------------------------
        db.commit()


# ============================================================
# CLEAR MEMORY
# ============================================================
#
# Purpose:
# Delete:
# - All messages
# - Session record
#
# Example:
#
# DELETE /chat/history/session_001
#
# ============================================================
def clear_memory(session_id: str) -> None:
    """Delete all messages and the session for a given session_id."""
    with SessionLocal() as db:
        
        # ----------------------------------------------------
        # Delete chat messages
        #
        # DELETE FROM chat_messages
        # WHERE session_id = ?
        # ----------------------------------------------------
        db.query(ChatMessage).filter(ChatMessage.session_id == session_id).delete()
        # ----------------------------------------------------
        # Delete session
        #
        # DELETE FROM chat_sessions
        # WHERE id = ?
        # ----------------------------------------------------
        db.query(ChatSession).filter(ChatSession.id == session_id).delete()
        # Save changes
        db.commit()


# ============================================================
# LIST ALL CHAT SESSIONS
# ============================================================
#
# Purpose:
# Populate sidebar conversations.
#
# Example:
#
# [
#   {
#     "session_id": "abc",
#     "title": "What is diabetes?",
#     "updated_at": "..."
#   }
# ]
#
# ============================================================
def list_sessions() -> list[dict]:
    """Return all sessions ordered by most recently updated, with title from first user message."""
    with SessionLocal() as db:
        
        # ----------------------------------------------------
        # Get all sessions
        #
        # ORDER BY updated_at DESC
        #
        # Recent chats appear first.
        # ----------------------------------------------------
        sessions = (
            db.query(ChatSession)
            .order_by(ChatSession.updated_at.desc())
            .all()
        )
        
        # Final response list
        result = []
        
        # ----------------------------------------------------
        # Process each session
        # ----------------------------------------------------
        for session in sessions:
            
            # ------------------------------------------------
            # Find first user message
            #
            # Used as chat title.
            #
            # Example:
            #
            # User:
            # "What is diabetes?"
            #
            # Sidebar title:
            # "What is diabetes?"
            #
            # ------------------------------------------------
            first_msg = (
                db.query(ChatMessage)
                .filter(ChatMessage.session_id == session.id, ChatMessage.role == "user")
                .order_by(ChatMessage.created_at)
                .first()
            )
            
            # ------------------------------------------------
            # Extract message text
            # ------------------------------------------------
            content = first_msg.content if first_msg else ""
            
            # ------------------------------------------------
            # Create shortened title
            #
            # Max length:
            # 38 chars
            #
            # Example:
            #
            # "What are symptoms of diabetes?"
            #
            # ------------------------------------------------
            title = (content[:38] + "…") if len(content) > 38 else content
            
            # ------------------------------------------------
            # Add session info
            # ------------------------------------------------
            result.append({
                "session_id": session.id,
                "title": title,
                "created_at": session.created_at.isoformat(),
                "updated_at": session.updated_at.isoformat(),
            })
        return result
