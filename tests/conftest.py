"""
Pytest configuration and shared fixtures for vector service tests.
"""

import pytest
import asyncio
import os
from unittest.mock import patch, MagicMock

# Set test environment variables
os.environ.update({
    "OPENAI_API_KEY": "test-openai-key",
    "PINECONE_API_KEY": "test-pinecone-key", 
    "PINECONE_ENVIRONMENT": "test-env",
    "PINECONE_INDEX_NAME": "test-index",
    "PINECONE_NAMESPACE": "test-namespace",
    "VECTOR_DIMENSIONS": "1536",
    "BATCH_SIZE": "5",
    "MAX_RETRIES": "2"
})


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(autouse=True)
def mock_env_vars():
    """Automatically mock environment variables for all tests."""
    with patch.dict(os.environ, {
        "OPENAI_API_KEY": "test-openai-key",
        "PINECONE_API_KEY": "test-pinecone-key",
        "PINECONE_ENVIRONMENT": "test-env",
        "PINECONE_INDEX_NAME": "test-index", 
        "PINECONE_NAMESPACE": "test-namespace"
    }):
        yield


@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client."""
    mock_client = MagicMock()
    mock_client.embeddings.create = MagicMock()
    return mock_client


@pytest.fixture 
def mock_pinecone_client():
    """Mock Pinecone client."""
    mock_client = MagicMock()
    mock_index = MagicMock()
    mock_client.Index.return_value = mock_index
    mock_client.list_indexes.return_value.indexes = [MagicMock(name="test-index")]
    return mock_client, mock_index


# Pytest async configuration
pytest_plugins = ('pytest_asyncio',) 