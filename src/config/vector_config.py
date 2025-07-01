import os
from dotenv import load_dotenv

load_dotenv()

# OpenAI Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "text-embedding-3-small")

OPENAI_CHAT_MODEL = os.getenv("OPENAI_CHAT_MODEL", "gpt-4o-mini")

# Pinecone Configuration
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_ENVIRONMENT = os.getenv("PINECONE_ENVIRONMENT")
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "football-news")
PINECONE_NAMESPACE = os.getenv("PINECONE_NAMESPACE", "articles")

# Redis Configuration
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_DB = int(os.getenv("REDIS_DB", "0"))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD")

# Processing Configuration
VECTOR_DIMENSIONS = int(os.getenv("VECTOR_DIMENSIONS", "1536"))
BATCH_SIZE = int(os.getenv("BATCH_SIZE", "10"))
PROCESSING_INTERVAL = int(os.getenv("PROCESSING_INTERVAL", "30"))
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))

# LangSmith Configuration
LANGSMITH_TRACING = os.getenv("LANGSMITH_TRACING", "true").lower() == "true"
LANGSMITH_ENDPOINT = os.getenv("LANGSMITH_ENDPOINT", "https://api.smith.langchain.com")
LANGSMITH_API_KEY = os.getenv("LANGSMITH_API_KEY")
LANGSMITH_PROJECT = os.getenv("LANGSMITH_PROJECT", "football-db")

# Validation function (called when VectorService is instantiated)
def validate_ai_config():
    """Validate AI configuration when VectorService is instantiated."""
    required_vars = [OPENAI_API_KEY, PINECONE_API_KEY, PINECONE_ENVIRONMENT]
    missing = [name for name, value in zip(['OPENAI_API_KEY', 'PINECONE_API_KEY', 'PINECONE_ENVIRONMENT'], required_vars) if not value]
    if missing:
        raise ValueError(f"Missing required environment variables for AI features: {missing}") 