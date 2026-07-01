import os
import sys

# --- THE ULTIMATE DEVELOPER HACK START ---
try:
    import langchain_core.document_loaders.base
    import langchain_core.document_loaders

    langchain_core.document_loaders.BaseBlobParser = langchain_core.document_loaders.base.BaseBlobParser
    langchain_core.document_loaders.BaseLoader = langchain_core.document_loaders.base.BaseLoader
    sys.modules['langchain_core.document_loaders'] = langchain_core.document_loaders
except Exception:
    pass
# --- THE ULTIMATE DEVELOPER HACK END ---

from langchain_community.document_loaders import PyMuPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from core.config import CHUNK_SIZE, CHUNK_OVERLAP
from core.vector_store import get_vector_store


def process_and_store_documents(file_paths, category="General"):
    """Processes dynamically uploaded PDFs, tags them, and updates ChromaDB"""
    documents = []

    try:
        for file_path in file_paths:
            loader = PyMuPDFLoader(file_path)
            loaded_docs = loader.load()

            # ATTACH METADATA TAG TO EVERY PAGE
            for doc in loaded_docs:
                # Sirf wahi pages add karein jinme sach mein text ho
                if doc.page_content and doc.page_content.strip() != "":
                    doc.metadata["category"] = category
                    documents.append(doc)

        if not documents:
            return False, "PDF mein koi readable text nahi mila. Shayad yeh ek scanned image hai ya blank document hai."

        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
            separators=["\n\n", "\n", ".", " ", ""]
        )
        chunks = text_splitter.split_documents(documents)

        # FINAL SAFETY CHECK: Agar splitting ke baad bhi chunks empty hain
        if not chunks or len(chunks) == 0:
            return False, "Documents se data extract nahi ho paaya. Please koi text-based PDF try karein."

        db = get_vector_store()
        db.add_documents(chunks)

        return True, f"Successfully Processed {len(file_paths)} files under '{category}'! ({len(chunks)} chunks generated)"
    except Exception as e:
        return False, f"Error processing documents: {str(e)}"