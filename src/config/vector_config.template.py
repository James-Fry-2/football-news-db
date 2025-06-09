import os
from dotenv import load_dotenv

load_dotenv()

# OpenAI Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "text-embedding-3-small")

# Pinecone Configuration
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_ENVIRONMENT = os.getenv("PINECONE_ENVIRONMENT")
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "football-news")
PINECONE_NAMESPACE = os.getenv("PINECONE_NAMESPACE", "articles")

# Processing Configuration
VECTOR_DIMENSIONS = int(os.getenv("VECTOR_DIMENSIONS", "1536"))
BATCH_SIZE = int(os.getenv("BATCH_SIZE", "10"))
PROCESSING_INTERVAL = int(os.getenv("PROCESSING_INTERVAL", "30"))
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))

# Validation
required_vars = [OPENAI_API_KEY, PINECONE_API_KEY, PINECONE_ENVIRONMENT]
if not all(required_vars):
    missing = [name for name, value in zip(['OPENAI_API_KEY', 'PINECONE_API_KEY', 'PINECONE_ENVIRONMENT'], required_vars) if not value]
    raise ValueError(f"Missing required environment variables: {missing}")