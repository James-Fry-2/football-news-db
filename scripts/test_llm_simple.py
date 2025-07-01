#!/usr/bin/env python3
"""
Simple test script to verify LLM service works without LangSmith issues
"""

import os
import sys
import asyncio
sys.path.append('src')

# Disable LangSmith tracing for this test
os.environ["LANGSMITH_TRACING"] = "false"
os.environ["LANGCHAIN_TRACING_V2"] = "false"
os.environ["LANGCHAIN_CALLBACKS_DISABLE"] = "true"

async def test_llm_service():
    """Test LLM service without LangSmith"""
    print("=== LLM Service Test (No LangSmith) ===\n")
    
    try:
        from db.database import get_db_session
        from db.services.llm_service import LLMService
        
        print("1. Testing database connection...")
        async with get_db_session() as session:
            print("✓ Database connected")
            
            print("\n2. Testing LLM service initialization...")
            llm_service = LLMService(session=session)
            print("✓ LLM service initialized")
            
            print(f"  Agent executor: {'✓ Available' if llm_service.agent_executor else '✗ Not available'}")
            print(f"  LLM model: {llm_service.llm.model_name}")
            
            print("\n3. Testing simple chat...")
            test_message = "Hello, can you tell me about football?"
            
            try:
                response_generator = llm_service.chat(test_message)
                response = ""
                async for chunk in response_generator:
                    response += chunk
                
                print(f"✓ Chat response received (length: {len(response)})")
                print(f"Response preview: {response[:200]}...")
                
            except Exception as e:
                print(f"✗ Chat error: {e}")
                import traceback
                traceback.print_exc()
                
    except Exception as e:
        print(f"✗ Test error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_llm_service()) 