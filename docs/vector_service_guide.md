# Vector Service Guide

The VectorService provides semantic search capabilities for football news articles using OpenAI embeddings and Pinecone vector storage.

## Features

- **OpenAI Embeddings**: Automatically generate embeddings using OpenAI's `text-embedding-3-small` model
- **Pinecone Storage**: Store vectors in Pinecone with metadata for fast similarity search
- **Semantic Search**: Query articles using natural language with similarity scoring
- **Batch Processing**: Process multiple articles efficiently with concurrency control
- **Error Handling**: Robust error handling with retry logic and status tracking
- **Sentiment Analysis**: Simple sentiment scoring for articles
- **Background Tasks**: Celery integration for processing articles asynchronously

## Setup

### 1. Environment Variables

Add these variables to your `.env` file:

```bash
# OpenAI Configuration
OPENAI_API_KEY=your-openai-api-key-here
OPENAI_MODEL=text-embedding-3-small

# Pinecone Configuration
PINECONE_API_KEY=your-pinecone-api-key-here
PINECONE_ENVIRONMENT=gcp-starter  # or your specific environment
PINECONE_INDEX_NAME=football-news
PINECONE_NAMESPACE=articles

# Processing Configuration
VECTOR_DIMENSIONS=1536
BATCH_SIZE=10
PROCESSING_INTERVAL=30
MAX_RETRIES=3
```

### 2. Install Dependencies

The required dependencies are already included in `requirements/llm.txt`:

```bash
pip install -r requirements/llm.txt
```

Key dependencies:
- `pinecone>=3.0.0` - Pinecone vector database client
- `openai>=1.0.0` - OpenAI API client for embeddings
- `asyncio` - For async/await patterns


The VectorService will automatically create the Pinecone index if it doesn't exist. You can also run the setup script manually:

```bash
python scripts/setup_pinecone.py
```

## Usage

### Direct Service Usage

```python
from src.db.database import get_async_session
from src.db.services.vector_service import VectorService

async def example_usage():
    async with get_async_session() as session:
        vector_service = VectorService(session)
        
        # Process a single article
        success, message = await vector_service.process_single_article(article_id=123)
        print(f"Processing result: {success}, {message}")
        
        # Process pending articles in batch
        stats = await vector_service.process_pending_articles(batch_size=10)
        print(f"Processed: {stats}")
        
        # Perform semantic search
        results = await vector_service.semantic_search(
            query="Manchester United transfer news",
            top_k=5,
            filter_dict={"source": "BBC Sport"}
        )
        
        for result in results:
            print(f"Score: {result['score']:.3f}")
            print(f"Title: {result['metadata']['title']}")
            print()
```

### Command Line Interface

Use the included script for processing and searching:

```bash
# Show processing statistics
python -m src.scripts.process_vectors --stats

# Process pending articles
python -m src.scripts.process_vectors --process-batch 20

# Process a specific article
python -m src.scripts.process_vectors --process-article 123

# Perform semantic search
python -m src.scripts.process_vectors --search "Liverpool Champions League" --top-k 10

# Search with source filter
python -m src.scripts.process_vectors --search "transfer news" --source "BBC Sport"
```

### API Endpoints

#### Semantic Search

```http
POST /api/vector-search/semantic-search
Content-Type: application/json

{
    "query": "Manchester United transfer news",
    "top_k": 5,
    "source_filter": "BBC Sport",
    "sentiment_filter": "positive"
}
```

Response:
```json
[
    {
        "id": "article_123",
        "score": 0.8542,
        "title": "Manchester United signs new midfielder",
        "url": "https://example.com/article/123",
        "source": "BBC Sport",
        "published_date": "2024-01-15T10:30:00Z",
        "sentiment": 0.75
    }
]
```

#### Processing Statistics

```http
GET /api/vector-search/processing-stats
```

Response:
```json
{
    "pending": 45,
    "processing": 2,
    "completed": 1523,
    "failed": 8,
    "total": 1578
}
```

#### Reprocess Article

```http
POST /api/vector-search/reprocess/123
```

## Background Processing

### Celery Tasks

The system includes Celery tasks for background processing:

```python
from src.tasks.vector_tasks import process_single_article_task, process_pending_vectors

# Queue single article for processing
task = process_single_article_task.delay(article_id=123)

# Process pending articles (can be scheduled)
process_pending_vectors.delay()
```

### Scheduled Processing

Add to your Celery beat schedule:

```python
from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    'process-pending-vectors': {
        'task': 'src.tasks.vector_tasks.process_pending_vectors',
        'schedule': crontab(minute='*/30'),  # Every 30 minutes
    },
}
```

## Article Processing Status

Articles have the following processing statuses:

- **pending**: Not yet processed
- **processing**: Currently being processed
- **completed**: Successfully processed and stored in Pinecone
- **failed**: Processing failed (will be retried)

## Error Handling

The VectorService includes comprehensive error handling:

- **Rate Limiting**: Automatic retry with exponential backoff for OpenAI API rate limits
- **API Errors**: Retry logic for transient OpenAI API errors
- **Pinecone Errors**: Graceful handling of Pinecone storage failures
- **Status Tracking**: Articles maintain processing status in the database
- **Recovery**: Stuck processing articles can be reset to pending

### Reset Stuck Articles

```python
# Reset articles stuck in 'processing' status
reset_count = await vector_service.reset_processing_status()
print(f"Reset {reset_count} articles")
```

## Monitoring

### Processing Statistics

```python
stats = await vector_service.get_processing_stats()
print(f"Completion rate: {stats['completed'] / stats['total'] * 100:.1f}%")
```

### Logs

The service uses loguru for structured logging:

```python
from loguru import logger

# Logs include:
# - Processing start/completion
# - Error details with context
# - Search query results
# - Rate limiting events
```

## Performance Considerations

### Concurrency

- The service limits concurrent OpenAI API calls to avoid rate limits
- Batch processing uses semaphore (max 3 concurrent requests)
- Small delays between requests to be API-friendly

### Pinecone Limitations

- Metadata values are truncated to stay within Pinecone limits
- URLs and titles limited to 512 characters
- Namespace isolation for different content types

### Token Limits

- Text is automatically truncated to ~8000 characters for embedding
- Longer articles have "..." appended after truncation

## Troubleshooting

### Common Issues

1. **Missing Environment Variables**
   ```
   ValueError: Missing required environment variables: ['OPENAI_API_KEY']
   ```
   Solution: Ensure all required environment variables are set in `.env`

2. **Pinecone Index Not Found**
   ```
   Error: Index 'football-news' not found
   ```
   Solution: The service will auto-create the index, or run setup script manually

3. **OpenAI Rate Limits**
   ```
   Rate limit exceeded after 3 retries
   ```
   Solution: Reduce batch size or increase delays between requests

4. **Articles Stuck in Processing**
   ```python
   # Reset stuck articles
   await vector_service.reset_processing_status()
   ```

### Debug Mode

Enable debug logging:

```python
from loguru import logger
logger.add("vector_processing.log", level="DEBUG")
```

## Best Practices

1. **Batch Processing**: Process articles in small batches (10-20) to avoid rate limits
2. **Monitor Status**: Regularly check processing statistics
3. **Error Recovery**: Reset stuck processing articles after system restarts
4. **Content Updates**: Articles are re-processed if content changes (via content hash)
5. **Filtering**: Use metadata filters to narrow search results effectively

## Integration Examples

### Automatic Processing

```python
# In your article creation workflow
async def create_article(article_data):
    # Create article in database
    article = await create_article_in_db(article_data)
    
    # Queue for vector processing
    from src.tasks.vector_tasks import process_single_article_task
    process_single_article_task.delay(article.id)
    
    return article
```

### Search Integration

```python
# In your search endpoint
async def search_articles(query: str, filters: dict = None):
    async with get_async_session() as session:
        vector_service = VectorService(session)
        
        # Get semantic results
        vector_results = await vector_service.semantic_search(
            query=query,
            top_k=10,
            filter_dict=filters
        )
        
        # Combine with traditional search if needed
        # ...
        
        return combine_results(vector_results, text_results)
``` 