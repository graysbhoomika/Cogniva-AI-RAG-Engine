import os
from dotenv import load_dotenv

# Load environment variables (API keys)
load_dotenv()

# --- API KEYS ---
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "YAHAN_APNA_API_KEY_DAALEIN_AGAR_ENV_NAHI_HAI")

# --- DIRECTORY PATHS ---
# Naye web app ke liye directories set karna zaroori hai
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOURCE_DOCS_DIR = os.path.join(BASE_DIR, "data", "source_docs")
CHROMA_DB_DIR = os.path.join(BASE_DIR, "data", "chroma_db")

# --- RAG PARAMETERS ---
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200