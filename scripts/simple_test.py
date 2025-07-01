#!/usr/bin/env python3
# scripts/simple_test.py

import asyncio
import aiohttp
import json

API_BASE_URL = "http://localhost:8000"

async def simple_test():
    """Simple test to isolate the issue."""
    
    async with aiohttp.ClientSession() as session:
        
        print("Testing basic connectivity...")
        
        # 1. Test root endpoint
        try:
            async with session.get(f"{API_BASE_URL}/") as response:
                print(f"Root endpoint: {response.status}")
                if response.status == 200:
                    data = await response.json()
                    print(f"Response: {data}")
        except Exception as e:
            print(f"Root endpoint error: {e}")
            return
        
        # 2. Test health endpoint
        try:
            async with session.get(f"{API_BASE_URL}/health") as response:
                print(f"Health endpoint: {response.status}")
                if response.status == 200:
                    data = await response.json()
                    print(f"Health: {data}")
        except Exception as e:
            print(f"Health endpoint error: {e}")
        
        # 3. Test a simple chat request
        print("\nTesting chat endpoint...")
        try:
            url = f"{API_BASE_URL}/api/v1/chat/chat"
            data = {"message": "test"}
            
            async with session.post(url, json=data) as response:
                print(f"Chat endpoint status: {response.status}")
                
                # Print all headers
                print("Response headers:")
                for key, value in response.headers.items():
                    print(f"  {key}: {value}")
                
                # Print response body
                try:
                    if response.content_type == 'application/json':
                        response_data = await response.json()
                        print(f"Response body: {json.dumps(response_data, indent=2)}")
                    else:
                        text = await response.text()
                        print(f"Response text: {text[:500]}...")
                except Exception as e:
                    print(f"Could not read response: {e}")
                    
        except Exception as e:
            print(f"Chat endpoint error: {e}")

if __name__ == "__main__":
    asyncio.run(simple_test()) 