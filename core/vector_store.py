import os
# THE ULTIMATE KILL SWITCH: Hides GPU from PyTorch to ensure stability
os.environ["CUDA_VISIBLE_DEVICES"] = ""

from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from core.config import CHROMA_DB_DIR

def get_embedding_function():
    # Removed the strict 'device' kwargs that caused the meta tensor crash.
    # It will automatically and safely fall back to CPU.
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    )
    return embeddings

def get_vector_store():
    embedding_function = get_embedding_function()
    db = Chroma(
        persist_directory=CHROMA_DB_DIR,
        embedding_function=embedding_function
    )
    return db