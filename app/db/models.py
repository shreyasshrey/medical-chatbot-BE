# Import datetime class for storing timestamps
from datetime import datetime

# Import SQLAlchemy column types and constraints
from sqlalchemy import (
    Column,      # Represents a database table column
    DateTime,    # Datetime data type
    ForeignKey,  # Creates relationship between tables
    Integer,     # Integer data type
    String,      # String/VARCHAR data type
    Text         # Large text field
)

# Import Base class that all ORM models inherit from
from app.db.database import Base


# ============================================================
# CHAT SESSION TABLE
# ============================================================
#
# Represents a chat conversation/session.
#
# Example:
#
# Session 1
# ├── Message 1
# ├── Message 2
# └── Message 3
#
# Session 2
# ├── Message 1
# └── Message 2
#
# Each session can contain multiple messages.
#
# ============================================================
class ChatSession(Base):
    # Database table name
    __tablename__ = "chat_sessions"

    # --------------------------------------------------------
    # Session ID
    #
    # Primary Key
    #
    # Example:
    # "abc123"
    # "session-001"
    # "550e8400-e29b-41d4-a716-446655440000"
    #
    # Each session must be unique.
    # --------------------------------------------------------
    id = Column(String(255), primary_key=True)
    
    # --------------------------------------------------------
    # Session Creation Time
    #
    # Automatically populated when a new
    # ChatSession record is created.
    #
    # Example:
    # 2026-06-17 14:35:12
    # --------------------------------------------------------
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # --------------------------------------------------------
    # Last Updated Time
    #
    # Automatically updated whenever the row changes.
    #
    # Example:
    # User sends a new message
    # → updated_at changes automatically.
    #
    # Useful for:
    # - Sorting recent chats
    # - Session activity tracking
    # - Chat sidebar ordering
    # --------------------------------------------------------
    updated_at = Column(
        DateTime,
        # Initial value when record is created
        default=datetime.utcnow,
        # Automatically update timestamp on record update
        onupdate=datetime.utcnow,
        nullable=False,
    )


# ============================================================
# CHAT MESSAGE TABLE
# ============================================================
#
# Stores individual chat messages.
#
# Example:
#
# ID | Session_ID | Role      | Content
# -----------------------------------------
# 1  | abc123     | user      | Hi
# 2  | abc123     | assistant | Hello
# 3  | abc123     | user      | What is diabetes?
#
# ============================================================
class ChatMessage(Base):
    
    # Database table name
    __tablename__ = "chat_messages"

    # --------------------------------------------------------
    # Message ID
    #
    # Auto-incrementing primary key.
    #
    # Example:
    # 1
    # 2
    # 3
    # 4
    #
    # SQL automatically generates values.
    # --------------------------------------------------------
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # --------------------------------------------------------
    # Session ID (Foreign Key)
    #
    # Connects message to a chat session.
    #
    # ForeignKey:
    # chat_sessions.id
    #
    # Example:
    #
    # ChatSession:
    # id = "abc123"
    #
    # ChatMessage:
    # session_id = "abc123"
    #
    # --------------------------------------------------------
    session_id = Column(
        String(255),
        # Foreign key reference to chat_sessions table
        # ondelete="CASCADE" If session is deleted,
        # automatically delete all messages
        ForeignKey("chat_sessions.id", ondelete="CASCADE"),
        nullable=False,
        # Create DB index for faster lookups
        index=True,
    )
    
    # --------------------------------------------------------
    # Message Role
    #
    # Indicates who sent the message.
    #
    # Possible values:
    # "user" | "assistant"
    #
    # Examples:
    #
    # user:
    #   "What is hypertension?"
    #
    # assistant:
    #   "Hypertension is..."
    #
    # --------------------------------------------------------
    role = Column(String(20), nullable=False)
    
    # --------------------------------------------------------
    # Message Content
    #
    # Stores the actual text.
    #
    # Using Text instead of String because
    # responses can be very large.
    #
    # Example:
    # "What is diabetes?"
    #
    # or
    #
    # "Diabetes is a chronic condition..."
    #
    # --------------------------------------------------------
    content = Column(Text, nullable=False)
    
    # --------------------------------------------------------
    # Message Timestamp
    #
    # Automatically set when message is saved.
    #
    # Example:
    #
    # 2026-06-17 15:42:10
    #
    # Used for:
    # - Sorting messages
    # - Displaying chat timeline
    # - Conversation history
    #
    # --------------------------------------------------------
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
