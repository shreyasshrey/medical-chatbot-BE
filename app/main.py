# Import asynccontextmanager to manage application startup and shutdown events
from contextlib import asynccontextmanager

# Import FastAPI framework
from fastapi import FastAPI
# Import CORS middleware to allow frontend applications to access backend APIs
from fastapi.middleware.cors import CORSMiddleware

# Import API router that contains all application endpoints
from app.api.routes import router
# Import database components:
# Base -> SQLAlchemy base model class
# engine -> Database connection engine
# ensure_database_exists -> Custom function to create database if it doesn't exist
from app.db.database import Base, engine, ensure_database_exists

# Define application lifespan events (startup and shutdown)
@asynccontextmanager
async def lifespan(_: FastAPI):
    """
    Runs when the application starts and stops.

    Startup:
    - Create database if it doesn't exist.
    - Create tables defined in SQLAlchemy models.

    Shutdown:
    - No special cleanup required currently.
    """

    # Create the database if it does not already exist
    ensure_database_exists()
    # Create all tables defined in SQLAlchemy models.
    # If tables already exist, this operation does nothing.
    Base.metadata.create_all(bind=engine)
    # Yield control back to FastAPI and keep application running
    yield

    # Code after yield would execute during application shutdown
    # Example:
    # close database connections
    # release resources
    # cleanup background tasks

# Create FastAPI application instance
app = FastAPI(
    title="Medical RAG Chatbot",  # Application title shown in Swagger UI
    lifespan=lifespan            # Register startup/shutdown lifecycle handler
)

# Add CORS middleware to allow requests from frontend applications
app.add_middleware(
    CORSMiddleware,
    # Allow requests only from React application running on localhost:3000
    allow_origins=["http://localhost:3000"],
     # Allow cookies, authorization headers, and credentials to be included in requests
    allow_credentials=True,
    # Allow all HTTP methods (GET, POST, PUT, DELETE, etc.)
    allow_methods=["*"],
    # Allow all request headers
    allow_headers=["*"],
)

# Register all API routes from router
# Example:
# /chat
# etc.
app.include_router(router)


@app.get("/health")
def health():
    return {"status": "ok"}
