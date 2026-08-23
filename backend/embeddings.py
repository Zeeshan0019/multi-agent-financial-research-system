import os
import logging
from langchain_community.embeddings import HuggingFaceEmbeddings

logger = logging.getLogger("shared_embeddings")

_embeddings = None

def get_shared_embeddings():
    global _embeddings
    if _embeddings is None:
        logger.info("Initializing shared HuggingFace sentence-transformers embeddings...")
        model_name = "sentence-transformers/all-MiniLM-L6-v2"
        # Using local_files_only=True avoids slow network calls on initialization
        _embeddings = HuggingFaceEmbeddings(
            model_name=model_name,
            model_kwargs={"local_files_only": True}
        )
        logger.info("Shared embeddings initialized successfully.")
    return _embeddings
