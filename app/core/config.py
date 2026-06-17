import os
from urllib.parse import quote_plus

from dotenv import load_dotenv

load_dotenv()

MODEL_NAME = os.getenv("MODEL_NAME", "Qwen/Qwen2.5-7B-Instruct")

EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "BAAI/bge-m3")

CHROMA_DIR = os.getenv("CHROMA_DIR", "./data/chroma_db")

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))

TEMPERATURE = float(os.getenv("TEMPERATURE", "0.2"))
MAX_NEW_TOKENS = int(os.getenv("MAX_NEW_TOKENS", "512"))

TOP_K_RETRIEVAL = int(os.getenv("TOP_K_RETRIEVAL", "10"))
TOP_K_RERANK = int(os.getenv("TOP_K_RERANK", "5"))

# MySQL
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "root@123")
DB_NAME = os.getenv("DB_NAME", "medical_chatbot")
DB_URL = (
    os.getenv("DB_URL")
    or f"mysql+pymysql://{DB_USER}:{quote_plus(DB_PASSWORD)}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)