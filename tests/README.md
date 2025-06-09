# VectorService Testing Guide

This directory contains comprehensive tests for the VectorService, covering unit tests, integration tests, and manual testing with real APIs.

## 📁 Test Structure

```
tests/
├── __init__.py                    # Test package initialization
├── conftest.py                    # Pytest configuration and shared fixtures
├── test_vector_service.py         # Unit tests (mocked externals)
├── test_vector_integration.py     # Integration tests (real DB, mocked APIs)
├── test_vector_manual.py          # Manual tests (real APIs)
├── test_runner.py                 # Test runner script
├── requirements.txt               # Test dependencies (generated)
└── README.md                      # This guide
```

## 🚀 Quick Start

### 1. Install Test Dependencies

```bash
# Generate test requirements file
python tests/test_runner.py requirements

# Install dependencies
pip install -r tests/requirements.txt
```

### 2. Run Tests

```bash
# Run unit tests (recommended for development)
python tests/test_runner.py unit

# Run integration tests
python tests/test_runner.py integration

# Run all available tests
python tests/test_runner.py all
```

## 📋 Test Types

### Unit Tests (`test_vector_service.py`)

**Purpose**: Test individual methods with mocked external dependencies
**Speed**: Fast (< 10 seconds)
**Requirements**: No API keys needed

**What's tested**:
- ✅ VectorService initialization
- ✅ Embedding generation with retry logic
- ✅ Pinecone vector storage and deletion
- ✅ Sentiment analysis calculations
- ✅ Article processing workflow
- ✅ Batch processing with concurrency
- ✅ Semantic search functionality
- ✅ Error handling and edge cases
- ✅ Processing statistics
- ✅ Utility functions

**Example**:
```bash
python tests/test_runner.py unit --verbose
```

### Integration Tests (`test_vector_integration.py`)

**Purpose**: Test complete workflows with real database operations
**Speed**: Medium (30-60 seconds)
**Requirements**: No API keys needed (APIs are mocked)

**What's tested**:
- ✅ Full article processing pipeline with database
- ✅ Batch processing with database transactions
- ✅ Processing statistics from real database
- ✅ Status reset functionality
- ✅ Content hash deduplication
- ✅ Error handling with database rollback
- ✅ Sentiment analysis with database storage

**Example**:
```bash
python tests/test_runner.py integration
```

### Manual Tests (`test_vector_manual.py`)

**Purpose**: Test against real OpenAI and Pinecone APIs
**Speed**: Slow (2-5 minutes, depends on API response times)
**Requirements**: Requires API keys

**What's tested**:
- ✅ Real OpenAI embedding generation
- ✅ Real Pinecone vector operations
- ✅ End-to-end article processing
- ✅ Real semantic search with embeddings
- ✅ API error handling and retries

**Setup**:
```bash
# Set environment variables
export OPENAI_API_KEY="your-openai-api-key"
export PINECONE_API_KEY="your-pinecone-api-key"
export PINECONE_ENVIRONMENT="your-pinecone-environment"

# Run manual tests
python tests/test_runner.py manual
```

## 🔧 Configuration

### Environment Variables for Testing

```bash
# Required for manual tests only
OPENAI_API_KEY=your-openai-api-key
PINECONE_API_KEY=your-pinecone-api-key
PINECONE_ENVIRONMENT=your-pinecone-environment

# Optional (have defaults)
PINECONE_INDEX_NAME=football-news-test
PINECONE_NAMESPACE=test-articles
VECTOR_DIMENSIONS=1536
BATCH_SIZE=5
MAX_RETRIES=2
```

### Test Database

- Unit tests: Use mocked database sessions
- Integration tests: Use SQLite in-memory database
- Manual tests: Use SQLite in-memory database with real APIs

## 📊 Test Coverage

The test suite covers all major VectorService functionality:

| Component | Unit Tests | Integration Tests | Manual Tests |
|-----------|------------|-------------------|--------------|
| Initialization | ✅ | ✅ | ✅ |
| Embedding Generation | ✅ | ✅ | ✅ |
| Pinecone Operations | ✅ | ✅ | ✅ |
| Article Processing | ✅ | ✅ | ✅ |
| Batch Processing | ✅ | ✅ | ✅ |
| Semantic Search | ✅ | ✅ | ✅ |
| Sentiment Analysis | ✅ | ✅ | ✅ |
| Error Handling | ✅ | ✅ | ✅ |
| Statistics | ✅ | ✅ | ✅ |
| Database Operations | - | ✅ | ✅ |
| Real API Integration | - | - | ✅ |

## 🛠 Test Runner Options

### Basic Usage

```bash
# Run specific test type
python tests/test_runner.py [unit|integration|manual|all]

# Run with verbose output
python tests/test_runner.py unit --verbose

# Run code linting
python tests/test_runner.py lint
```

### Advanced Usage

```bash
# Run pytest directly with custom options
python -m pytest tests/test_vector_service.py -v -k "test_sentiment"

# Run specific test class
python -m pytest tests/test_vector_service.py::TestVectorServiceSentiment -v

# Run with coverage reporting (if pytest-cov installed)
python -m pytest tests/ --cov=src.db.services.vector_service --cov-report=html
```

## 🐛 Debugging Tests

### Common Issues

1. **Missing Dependencies**
   ```bash
   # Install all test dependencies
   pip install -r tests/requirements.txt
   ```

2. **API Key Issues** (Manual tests only)
   ```bash
   # Check environment variables
   echo $OPENAI_API_KEY
   echo $PINECONE_API_KEY
   ```

3. **Import Errors**
   ```bash
   # Make sure you're running from project root
   cd /path/to/football-news-db
   python tests/test_runner.py unit
   ```

### Debug Modes

```bash
# Run with maximum verbosity
python tests/test_runner.py unit --verbose

# Run single test with debugging
python -m pytest tests/test_vector_service.py::TestVectorServiceSentiment::test_sentiment_positive -v -s

# Run with pdb debugging (add breakpoint() in code)
python -m pytest tests/test_vector_service.py -v -s --pdb
```

## 📈 Performance Testing

### Benchmark Article Processing

```python
# Add to manual tests to benchmark processing speed
import time

start_time = time.time()
stats = await service.process_batch(article_ids)
end_time = time.time()

processing_time = end_time - start_time
articles_per_second = len(article_ids) / processing_time

print(f"Processed {len(article_ids)} articles in {processing_time:.2f}s")
print(f"Rate: {articles_per_second:.2f} articles/second")
```

### Memory Usage Monitoring

```bash
# Install memory profiler
pip install memory-profiler

# Run with memory monitoring
python -m memory_profiler tests/test_vector_manual.py
```

## 🔄 Continuous Integration

### GitHub Actions Example

```yaml
name: Vector Service Tests
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
    
    - name: Run linting
      run: python tests/test_runner.py lint
```

## 📝 Writing New Tests

### Adding Unit Tests

```python
# In test_vector_service.py
class TestNewFeature:
    @pytest.mark.asyncio
    async def test_new_method(self, vector_service):
        # Arrange
        mock_data = "test data"
        
        # Act
        result = await vector_service.new_method(mock_data)
        
        # Assert
        assert result is not None
```

### Adding Integration Tests

```python
# In test_vector_integration.py
@pytest.mark.asyncio
async def test_new_workflow(self, test_session):
    # Test with real database operations
    # but mocked external APIs
    pass
```

### Adding Manual Tests

```python
# In test_vector_manual.py
async def test_new_api_feature(self):
    # Test with real APIs
    # Requires API keys
    pass
```

## 🎯 Best Practices

1. **Always run unit tests first** - they're fast and catch most issues
2. **Use integration tests for database workflows** - they catch transaction issues
3. **Use manual tests sparingly** - they consume API quota and are slower
4. **Mock external dependencies in unit/integration tests** - for reliability and speed
5. **Test error conditions** - ensure proper error handling
6. **Use descriptive test names** - make failures easy to understand
7. **Keep tests isolated** - each test should be independent

## 🚨 Safety Notes

- **Manual tests use real APIs** - they may consume API quota
- **Manual tests create/delete vectors in Pinecone** - use a test index
- **Set appropriate rate limits** - to avoid hitting API limits
- **Use test data only** - don't run tests against production data

## 📞 Support

If you encounter issues with the tests:

1. Check this README for common solutions
2. Verify your environment setup
3. Run tests with `--verbose` for more details
4. Check the individual test files for specific test requirements

The test suite is designed to be comprehensive yet easy to use. Start with unit tests for development, use integration tests for CI/CD, and run manual tests when you need to verify real API integration. 