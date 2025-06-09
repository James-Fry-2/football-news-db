import pinecone
from src.config.vector_config import (
    PINECONE_API_KEY, PINECONE_ENVIRONMENT, PINECONE_INDEX_NAME, VECTOR_DIMENSIONS
)

def setup_pinecone_index():
    """Create Pinecone index if it doesn't exist."""
    try:
        pinecone.init(api_key=PINECONE_API_KEY, environment=PINECONE_ENVIRONMENT)
        
        # Check if index exists
        if PINECONE_INDEX_NAME not in pinecone.list_indexes():
            print(f"Creating Pinecone index: {PINECONE_INDEX_NAME}")
            pinecone.create_index(
                name=PINECONE_INDEX_NAME,
                dimension=VECTOR_DIMENSIONS,
                metric="cosine",
                metadata_config={
                    "indexed": ["source", "sentiment"]
                }
            )
            print("✅ Pinecone index created successfully")
        else:
            print("✅ Pinecone index already exists")
            
    except Exception as e:
        print(f"❌ Error setting up Pinecone: {e}")
        raise

if __name__ == "__main__":
    setup_pinecone_index()