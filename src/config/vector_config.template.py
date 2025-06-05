"""
Vector service configuration template.
Copy this file to vector_config.py and replace the placeholder values with your actual credentials.
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# OpenAI API settings
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY environment variable is not set")

# Pinecone settings
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
if not PINECONE_API_KEY:
    raise ValueError("PINECONE_API_KEY environment variable is not set")

PINECONE_ENVIRONMENT = os.getenv("PINECONE_ENVIRONMENT")
if not PINECONE_ENVIRONMENT:
    raise ValueError("PINECONE_ENVIRONMENT environment variable is not set")

# Vector service settings
VECTOR_INDEX_NAME = os.getenv("VECTOR_INDEX_NAME", "football-news")
VECTOR_NAMESPACE = os.getenv("VECTOR_NAMESPACE", "articles")
VECTOR_DIMENSIONS = int(os.getenv("VECTOR_DIMENSIONS", "1536"))  # OpenAI text-embedding-3-small dimensions 