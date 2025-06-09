# Run the test script directly in the LLM container
docker-compose run --rm llm python -c "
from pinecone import Pinecone
import os
# Test Pinecone connection
try:
    print('🔌 Connecting to Pinecone...')
    pc = Pinecone(
        api_key=os.getenv('PINECONE_API_KEY')
    )
    
    indexes = pc.list_indexes()
    print(f'✅ Connected! Available indexes: {indexes}')
    
    # Test your specific index
    index = pc.Index('football-news-prod')
    stats = index.describe_index_stats()
    print(f'✅ Index stats: {stats}')
    
    print('✅ Pinecone connection successful!')
    
except Exception as e:
    print(f'❌ Connection failed: {e}')
    import traceback
    traceback.print_exc()
"