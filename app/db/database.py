# Import SQLAlchemy engine creation utility
# Engine manages database connections and communication with MySQL
from sqlalchemy import create_engine, text
# Import sessionmaker for creating database sessions
# Import DeclarativeBase as the base class for ORM models
from sqlalchemy.orm import sessionmaker, DeclarativeBase

# Import database configuration values from config file
from app.core.config import DB_HOST, DB_NAME, DB_PASSWORD, DB_PORT, DB_URL, DB_USER
# Used to safely encode special characters in passwords
from urllib.parse import quote_plus

# ============================================================
# DATABASE ENGINE
# ============================================================
#
# Engine is the main entry point for SQLAlchemy to communicate
# with the database.
#
# Example:
# mysql+pymysql://user:password@localhost:3306/medical_rag
#
# pool_pre_ping=True
#     Checks connection validity before using it.
#
# pool_recycle=3600
#     Recreates connection after 1 hour to avoid
#     MySQL timeout issues.
#
# ============================================================
engine = create_engine(DB_URL, pool_pre_ping=True, pool_recycle=3600)

# ============================================================
# SESSION FACTORY
# ============================================================
#
# SessionLocal creates database sessions.
#
# Each API request typically:
#     Open Session
#     Execute Queries
#     Commit/Rollback
#     Close Session
#
# autocommit=False
#     Transactions must be committed manually.
#
# autoflush=False
#     Changes are not automatically pushed to DB.
#
# bind=engine
#     Connect session to our MySQL engine.
#
# ============================================================
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# ============================================================
# BASE MODEL CLASS
# ============================================================
#
# All SQLAlchemy ORM models inherit from Base.
#
# Example:
#
# class ChatMessage(Base):
#     __tablename__ = "chat_messages"
#
#     id = Column(Integer, primary_key=True)
#
# SQLAlchemy uses this Base class to track all models.
#
# ============================================================
class Base(DeclarativeBase):
    pass


# ============================================================
# CREATE DATABASE IF NOT EXISTS
# ============================================================
#
# Purpose:
#     Ensure the database exists before creating tables.
#
# Flow:
#     1. Connect to MySQL Server
#     2. Check if database exists
#     3. Create database if missing
#     4. Close temporary connection
#
# ============================================================
def ensure_database_exists() -> None:
    """
    Connect to MySQL server without selecting a database
    and create the target database if it doesn't exist.
    """
    
    # --------------------------------------------------------
    # Build server-level connection URL
    # --------------------------------------------------------
    #
    # Notice:
    # No database name is included.
    #
    # Example:
    # mysql+pymysql://root:password@localhost:3306/
    #
    # quote_plus() safely encodes special characters
    # in passwords.
    #
    # Example:
    # password@123
    # becomes
    # password%40123
    #
    # --------------------------------------------------------
    server_url = (
        f"mysql+pymysql://{DB_USER}:{quote_plus(DB_PASSWORD)}@{DB_HOST}:{DB_PORT}/"
    )
    
    # --------------------------------------------------------
    # Create temporary engine
    # --------------------------------------------------------
    #
    # AUTOCOMMIT is required because
    # CREATE DATABASE cannot run inside transactions
    #
    # --------------------------------------------------------
    tmp_engine = create_engine(server_url, isolation_level="AUTOCOMMIT")
    
    # --------------------------------------------------------
    # Open connection
    # --------------------------------------------------------
    with tmp_engine.connect() as conn:
        
        # ----------------------------------------------------
        # Execute CREATE DATABASE statement
        # ----------------------------------------------------
        #
        # IF NOT EXISTS prevents errors if database
        # already exists.
        #
        # utf8mb4 supports:
        #     English
        #     Unicode
        #     Emojis
        #     Multilingual content
        #
        # utf8mb4_unicode_ci
        #     Case-insensitive collation
        #
        # ----------------------------------------------------
        conn.execute(
            text(
                f"CREATE DATABASE IF NOT EXISTS `{DB_NAME}` "
                "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
            )
        )
        
    # --------------------------------------------------------
    # Close all connections associated with temp engine
    # --------------------------------------------------------
    tmp_engine.dispose()
