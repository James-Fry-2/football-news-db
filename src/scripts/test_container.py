#!/usr/bin/env python3
"""
Simple test script to verify container environment.
"""

import os
import sys
from loguru import logger

def test_environment():
    """Test the container environment."""
    logger.info("🧪 Testing container environment...")
    
    # Test Python imports
    try:
        import sqlalchemy
        logger.info(f"✅ SQLAlchemy version: {sqlalchemy.__version__}")
    except ImportError as e:
        logger.error(f"❌ SQLAlchemy import failed: {e}")
        return False
    
    # Test database config
    try:
        from ..config.db_config import DATABASE_URL
        logger.info(f"✅ Database URL configured: {DATABASE_URL[:50]}...")
    except Exception as e:
        logger.error(f"❌ Database config failed: {e}")
        return False
    
    # Test database connection
    try:
        from ..db.database import Database, get_async_session
        logger.info("✅ Database modules imported successfully")
    except Exception as e:
        logger.error(f"❌ Database module import failed: {e}")
        return False
    
    # Test environment variables
    env_vars = ['POSTGRES_HOST', 'POSTGRES_DB', 'POSTGRES_USER']
    for var in env_vars:
        value = os.getenv(var, 'NOT_SET')
        logger.info(f"📝 {var}={value}")
    
    # Test AI config (without validation)
    logger.info("\n🤖 Testing AI configuration (import only)...")
    try:
        import importlib
        config_module = importlib.import_module('src.config.vector_config')
        logger.info(f"✅ Vector config imported successfully")
        
        # Check if AI environment variables exist
        ai_vars = ['OPENAI_API_KEY', 'PINECONE_API_KEY', 'PINECONE_ENVIRONMENT']
        for var in ai_vars:
            value = os.getenv(var, 'NOT_SET')
            status = "✅" if value and value != 'NOT_SET' else "⚠️ "
            logger.info(f"{status} {var}={'SET' if value and value != 'NOT_SET' else 'NOT_SET'}")
    
    except Exception as e:
        logger.error(f"❌ Vector config import failed: {e}")
        return False
    
    logger.info("\n🎉 Container environment test completed!")
    return True

if __name__ == "__main__":
    # Configure logging
    logger.remove()
    logger.add(sys.stdout, level="INFO")
    
    # Run test
    success = test_environment()
    sys.exit(0 if success else 1) 