# VectorService Testing Guide

This guide provides comprehensive instructions for testing the VectorService in its entirety, covering unit tests, integration tests, and manual testing scenarios.

## 🎯 Testing Overview

The VectorService handles:
- OpenAI embedding generation
- Pinecone vector storage and search
- Article processing and sentiment analysis
- Batch processing with error handling
- Database operations and transaction management

## 📋 Testing Strategies

### 1. Unit Tests (Recommended for Development)
Test individual methods with mocked external dependencies.

**Advantages:**
- Fast execution (< 10 seconds)
- No API keys required
- Isolated testing of logic
- Reliable and repeatable

**What to test:**
- Sentiment analysis algorithms
- Content hash generation
- Error handling logic
- Configuration validation

### 2. Integration Tests
Test complete workflows with real database but mocked APIs.

**Advantages:**
- Tests database transactions
- Validates data flow
- Catches integration issues
- No external API costs

**What to test:**
- Article processing pipeline
- Batch processing workflows
- Database state management
- Transaction rollbacks

### 3. Manual Tests (Production Validation)
Test against real OpenAI and Pinecone APIs.

**Advantages:**
- End-to-end validation
- Real API behavior testing
- Performance validation
- Production readiness check

**What to test:**
- Real embedding generation
- Actual vector operations
- API error handling
- Rate limiting behavior

## 🚀 Quick Start Testing

### Step 1: Install Dependencies

```bash
# Install test dependencies
pip install -r tests/requirements.txt

# Verify installation
python -c "import pytest; print('Tests ready!')"
```

### Step 2: Run Basic Tests

```bash
# Run simplified tests (no API keys needed)
python tests/test_vector_simple.py

# Run with pytest for better output
python -m pytest tests/test_vector_simple.py -v
```

### Step 3: Run Full Test Suite

```bash
# Run all unit tests
python tests/test_runner.py unit

# Run integration tests
python tests/test_runner.py integration

# Run everything available
python tests/test_runner.py all
```

## 🔧 Test Configuration

### Environment Variables

```bash
# For unit/integration tests (uses test values)
export OPENAI_API_KEY="test-key"
export PINECONE_API_KEY="test-key"
export PINECONE_ENVIRONMENT="test-env"

# For manual tests (requires real keys)
export OPENAI_API_KEY="your-real-openai-key"
export PINECONE_API_KEY="your-real-pinecone-key"
export PINECONE_ENVIRONMENT="your-pinecone-environment"
```

### Test Database Setup

The tests use SQLite in-memory databases, so no external database setup is required.

## 📖 Detailed Testing Scenarios

### Scenario 1: Testing Sentiment Analysis

```python
def test_sentiment_analysis():
    """Test sentiment analysis with various inputs."""
    service = create_mock_vector_service()
    
    # Test cases
    test_cases = [
        ("Great victory! Amazing performance!", "positive"),
        ("Terrible defeat and awful play", "negative"), 
        ("The match was played today", "neutral"),
        ("", "neutral")
    ]
    
    for text, expected in test_cases:
        score = service._calculate_simple_sentiment(text)
        
        if expected == "positive":
            assert score > 0
        elif expected == "negative":
            assert score < 0
        else:  # neutral
            assert score == 0.0
        
        # Always within valid range
        assert -1.0 <= score <= 1.0
```

### Scenario 2: Testing Embedding Generation

```python
@pytest.mark.asyncio
async def test_embedding_generation():
    """Test embedding generation with different text inputs."""
    service = create_mock_vector_service()
    
    # Test cases
    test_texts = [
        "Short text",
        "Medium length text about football and sports",
        "Very long text " * 1000,  # Test truncation
        "Text with special characters: @#$%^&*()",
        "Non-English text: Fußball ist großartig!"
    ]
    
    for text in test_texts:
        embedding = await service.generate_embedding(text)
        
        # Verify embedding properties
        assert isinstance(embedding, list)
        assert len(embedding) == 1536  # text-embedding-3-small
        assert all(isinstance(x, float) for x in embedding)
        assert any(x != 0 for x in embedding)  # Not all zeros
```

### Scenario 3: Testing Article Processing Pipeline

```python
@pytest.mark.asyncio
async def test_article_processing_pipeline():
    """Test complete article processing workflow."""
    
    # Create test article
    article = create_test_article(
        title="Manchester City Win",
        content="Great victory with excellent goals...",
        status="pending"
    )
    
    # Process article
    service = create_vector_service_with_mocks()
    success, message = await service.process_single_article(article.id)
    
    # Verify processing
    assert success is True
    assert "Successfully processed" in message
    
    # Check article updates
    updated_article = get_article_from_db(article.id)
    assert updated_article.embedding_status == "completed"
    assert updated_article.vector_embedding is not None
    assert updated_article.sentiment_score is not None
    assert updated_article.content_hash is not None
    assert updated_article.search_vector_id == f"article_{article.id}"
```

### Scenario 4: Testing Batch Processing

```python
@pytest.mark.asyncio
async def test_batch_processing():
    """Test batch processing of multiple articles."""
    
    # Create multiple test articles
    articles = create_test_articles(count=5, status="pending")
    article_ids = [a.id for a in articles]
    
    # Process batch
    service = create_vector_service_with_mocks()
    stats = await service.process_batch(article_ids)
    
    # Verify batch results
    assert stats["processed"] == 5
    assert stats["succeeded"] == 5
    assert stats["failed"] == 0
    assert len(stats["messages"]) == 5
    
    # Check all articles processed
    for article_id in article_ids:
        article = get_article_from_db(article_id)
        assert article.embedding_status == "completed"
```

### Scenario 5: Testing Error Handling

```python
@pytest.mark.asyncio
async def test_error_handling():
    """Test error handling in various failure scenarios."""
    
    service = create_vector_service_with_mocks()
    
    # Test OpenAI API failure
    service.generate_embedding = AsyncMock(side_effect=Exception("API Error"))
    success, message = await service.process_single_article(article_id)
    assert success is False
    assert "Failed to generate embedding" in message
    
    # Test Pinecone failure
    service.generate_embedding = AsyncMock(return_value=[0.1] * 1536)
    service.store_vector_in_pinecone = AsyncMock(return_value=False)
    success, message = await service.process_single_article(article_id)
    assert success is False
    assert "Failed to store vector" in message
    
    # Test database failure
    service.session.commit = AsyncMock(side_effect=Exception("DB Error"))
    success, message = await service.process_single_article(article_id)
    assert success is False
```

### Scenario 6: Testing Semantic Search

```python
@pytest.mark.asyncio
async def test_semantic_search():
    """Test semantic search functionality."""
    
    service = create_vector_service_with_mocks()
    
    # Mock search results
    mock_results = create_mock_search_results([
        {"id": "article_1", "score": 0.95, "metadata": {"title": "City Win"}},
        {"id": "article_2", "score": 0.87, "metadata": {"title": "Arsenal News"}}
    ])
    service.index.query.return_value = mock_results
    
    # Test search
    results = await service.semantic_search("Manchester City", top_k=2)
    
    # Verify results
    assert len(results) == 2
    assert results[0]["score"] > results[1]["score"]  # Sorted by relevance
    assert "City" in results[0]["metadata"]["title"]
    
    # Test with filters
    filter_dict = {"source": "BBC Sport"}
    await service.semantic_search("football", filter_dict=filter_dict)
    service.index.query.assert_called_with(
        vector=mock_embedding,
        top_k=5,
        namespace="test-namespace",
        include_metadata=True,
        filter=filter_dict
    )
```

## 🧪 Manual Testing with Real APIs

### Setup for Manual Testing

1. **Get API Keys:**
   ```bash
   # OpenAI API key from https://platform.openai.com/api-keys
   export OPENAI_API_KEY="sk-..."
   
   # Pinecone API key from https://app.pinecone.io/
   export PINECONE_API_KEY="..."
   export PINECONE_ENVIRONMENT="us-west1-gcp"
   ```

2. **Run Manual Tests:**
   ```bash
   python tests/test_runner.py manual
   ```

### Manual Test Checklist

- [ ] **Embedding Generation**: Can generate embeddings for sample text
- [ ] **Vector Storage**: Can store vectors in Pinecone
- [ ] **Vector Search**: Can retrieve similar vectors
- [ ] **Article Processing**: Can process real articles end-to-end
- [ ] **Batch Processing**: Can handle multiple articles efficiently
- [ ] **Error Recovery**: Handles API failures gracefully
- [ ] **Rate Limiting**: Respects API rate limits
- [ ] **Performance**: Processes articles within acceptable time

### Performance Benchmarks

```python
import time

async def benchmark_article_processing():
    """Benchmark article processing performance."""
    
    start_time = time.time()
    
    # Process 10 test articles
    article_ids = create_test_articles(count=10)
    stats = await service.process_batch(article_ids)
    
    end_time = time.time()
    processing_time = end_time - start_time
    
    # Calculate metrics
    articles_per_second = len(article_ids) / processing_time
    avg_time_per_article = processing_time / len(article_ids)
    
    print(f"Processed {len(article_ids)} articles in {processing_time:.2f}s")
    print(f"Rate: {articles_per_second:.2f} articles/second")
    print(f"Average: {avg_time_per_article:.2f}s per article")
    
    # Performance assertions
    assert articles_per_second > 0.5  # At least 0.5 articles/second
    assert avg_time_per_article < 10  # Less than 10 seconds per article
```

## 🔍 Debugging Tests

### Common Issues and Solutions

1. **Import Errors:**
   ```bash
   # Make sure you're in the project root
   cd /path/to/football-news-db
   python -m pytest tests/test_vector_simple.py
   ```

2. **API Key Issues:**
   ```bash
   # Check environment variables
   echo $OPENAI_API_KEY
   echo $PINECONE_API_KEY
   
   # For unit tests, use dummy values
   export OPENAI_API_KEY="test-key"
   export PINECONE_API_KEY="test-key"
   ```

3. **Async Test Issues:**
   ```bash
   # Install pytest-asyncio
   pip install pytest-asyncio
   
   # Run with proper async support
   python -m pytest tests/test_vector_simple.py -v
   ```

### Debug Mode

```bash
# Run with verbose output
python -m pytest tests/test_vector_simple.py -v -s

# Run specific test
python -m pytest tests/test_vector_simple.py::TestVectorServiceSimple::test_sentiment_analysis_positive -v

# Run with debugging
python -m pytest tests/test_vector_simple.py -v -s --pdb
```

### Logging

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Or use loguru (already used by VectorService)
from loguru import logger
logger.add("tests.log", level="DEBUG")
```

## 📊 Test Coverage

### What Should Be Tested

**Core Functionality (100% coverage):**
- ✅ Sentiment analysis algorithm
- ✅ Content hash generation
- ✅ Configuration validation
- ✅ Error handling logic

**Integration Points (80% coverage):**
- ✅ OpenAI API integration
- ✅ Pinecone operations
- ✅ Database transactions
- ✅ Batch processing

**Edge Cases (60% coverage):**
- ✅ Empty/invalid inputs
- ✅ API failures
- ✅ Network timeouts
- ✅ Malformed data

### Coverage Reporting

```bash
# Install coverage tools
pip install pytest-cov

# Run with coverage
python -m pytest tests/ --cov=src.db.services.vector_service --cov-report=html

# View coverage report
open htmlcov/index.html
```

## 🎯 Best Practices

### 1. Test Isolation
- Each test should be independent
- Use fresh mocks for each test
- Clean up resources after tests

### 2. Mock External Dependencies
- Always mock OpenAI and Pinecone in unit tests
- Use real database for integration tests
- Only use real APIs for manual validation

### 3. Test Error Conditions
- Test happy path and failure scenarios
- Verify error messages are helpful
- Ensure graceful degradation

### 4. Performance Testing
- Benchmark critical operations
- Test with realistic data volumes
- Monitor resource usage

### 5. Documentation
- Document test purposes clearly
- Include expected outcomes
- Provide troubleshooting steps

## 🚀 Continuous Integration

### GitHub Actions Example

```yaml
name: VectorService Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.9'
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install -r tests/requirements.txt
    
    - name: Run unit tests
      run: python tests/test_runner.py unit
    
    - name: Run integration tests
      run: python tests/test_runner.py integration
      
    - name: Upload coverage
      uses: codecov/codecov-action@v3
```

## 📞 Support and Troubleshooting

### Getting Help

1. **Check this guide** for common solutions
2. **Run simplified tests** first: `python tests/test_vector_simple.py`
3. **Check logs** for detailed error messages
4. **Verify environment** setup and dependencies

### Common Error Messages

**"ModuleNotFoundError: No module named 'openai'"**
- Solution: `pip install -r tests/requirements.txt`

**"Missing required environment variables"**
- Solution: Set test environment variables or real API keys

**"Pinecone index not found"**
- Solution: Tests create temporary indexes automatically

**"Rate limit exceeded"**
- Solution: Wait a moment and retry, or use mocked tests

### Performance Optimization

**Slow tests:**
- Use unit tests for development
- Run integration tests less frequently
- Use manual tests only for validation

**Memory issues:**
- Process articles in smaller batches
- Clean up test data after each test
- Monitor memory usage during tests

This guide provides a comprehensive approach to testing the VectorService. Start with the simplified tests, then move to more complex scenarios as needed. Remember that unit tests should be your primary tool during development, with integration and manual tests used for validation and production readiness. 