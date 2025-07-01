#!/usr/bin/env python3
# scripts/test_minimal.py

import asyncio
import aiohttp

async def test_minimal():
    """Test minimal functionality."""
    
    async with aiohttp.ClientSession() as session:
        
        print("Testing minimal endpoints...")
        
        # Test health
        try:
            async with session.get("http://localhost:8000/health") as response:
                print(f"Health: {response.status}")
                if response.status == 200:
                    data = await response.json()
                    print(f"  Data: {data}")
                else:
                    text = await response.text()
                    print(f"  Error: {text}")
        except Exception as e:
            print(f"Health endpoint failed: {e}")
        
        # Test docs
        try:
            async with session.get("http://localhost:8000/docs") as response:
                print(f"Docs: {response.status}")
        except Exception as e:
            print(f"Docs endpoint failed: {e}")
        
        # Test a simple articles endpoint (shouldn't need OpenAI)
        try:
            async with session.get("http://localhost:8000/api/v1/articles") as response:
                print(f"Articles: {response.status}")
                if response.status != 200:
                    text = await response.text()
                    print(f"  Articles error: {text[:200]}")
        except Exception as e:
            print(f"Articles endpoint failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_minimal()) 