"""
Configuration file for books Q&A system.
Loads environment variables and sets up configuration.
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Pinecone Configuration
PINECONE_API_KEY = os.environ.get("PINECONE_API_KEY")
PINECONE_ENV = os.environ.get("PINECONE_ENV")  # Only needed for older Pinecone SDK
PINECONE_INDEX = os.environ.get("PINECONE_INDEX", "books-knowledge")
PINECONE_CLOUD = os.environ.get("PINECONE_CLOUD", "aws")  # "aws" or "gcp"
PINECONE_REGION = os.environ.get("PINECONE_REGION", "us-east-1")  # e.g., "us-east-1", "us-west-2"

# Google Gen AI Configuration
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")

# Model Configuration
# For new Google Gen AI SDK: use "text-embedding-004" or "embedding-gecko-001" (without "models/" prefix)
# For Vertex AI: use "textembedding-gecko@001" or "textembedding-gecko@003"
# The code will automatically add "models/" prefix if needed
EMBEDDING_MODEL = os.environ.get("EMBEDDING_MODEL", "text-embedding-004")
GENERATION_MODEL = os.environ.get("GENERATION_MODEL", "gemini-2.0-flash-exp")

# Retrieval Configuration
SIMILARITY_THRESHOLD = float(os.environ.get("SIMILARITY_THRESHOLD", "0.3"))  # Lowered from 0.75 to 0.5 for better retrieval
TOP_K = int(os.environ.get("TOP_K", "5"))

# Text Splitting Configuration
CHUNK_SIZE = int(os.environ.get("CHUNK_SIZE", "1000"))
CHUNK_OVERLAP = int(os.environ.get("CHUNK_OVERLAP", "200"))

# Batch Processing Configuration
BATCH_SIZE = int(os.environ.get("BATCH_SIZE", "50"))

# System Prompt for Strict QA
SYSTEM_PROMPT = (
    "You are a question-answering assistant whose knowledge is strictly limited to the provided document excerpts. "
    "Answer the user's question using ONLY the provided excerpts. If the answer is not in those excerpts, "
    'respond exactly: "I don\'t know — that information is not in my knowledge (the books)." '
    "When you answer, include a short citation with the source book name and chunk_id."
)

# Validate required environment variables
def validate_config():
    """Validate that required environment variables are set."""
    required_vars = {
        "PINECONE_API_KEY": PINECONE_API_KEY,
    }
    
    missing = [var for var, value in required_vars.items() if not value]
    if missing:
        raise ValueError(
            f"Missing required environment variables: {', '.join(missing)}\n"
            "Get your Pinecone API key from: https://app.pinecone.io/ -> API Keys section"
        )
    
    # PINECONE_ENV is only required for older Pinecone SDK
    # Newer serverless version doesn't need it
    
    return True

