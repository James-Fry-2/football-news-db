#!/usr/bin/env python3
# scripts/debug_rate_limiter.py

import asyncio
import aiohttp
import json
import sys
from datetime import datetime

# Configuration
API_BASE_URL = "http://localhost:8000"
ADMIN_TOKEN = "admin_token_123"


async def debug_api_health():
    """Check if the API is responding to basic requests."""
    print("=== API Health Check ===")
    
    async with aiohttp.ClientSession() as session:
        
        # 1. Test root endpoint
        try:
            async with session.get(f"{API_BASE_URL}/") as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✓ Root endpoint: {data.get('message', 'OK')}")
                else:
                    print(f"✗ Root endpoint failed: {response.status}")
                    return False
        except Exception as e:
            print(f"✗ Cannot connect to API: {e}")
            print("Make sure the API server is running on http://localhost:8000")
            return False
        
        # 2. Test health endpoint
        try:
            async with session.get(f"{API_BASE_URL}/health") as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✓ Health endpoint: {data.get('status', 'OK')}")
                else:
                    print(f"✗ Health endpoint failed: {response.status}")
        except Exception as e:
            print(f"✗ Health endpoint error: {e}")
        
        # 3. Test a simple non-rate-limited endpoint
        try:
            async with session.get(f"{API_BASE_URL}/docs") as response:
                if response.status == 200:
                    print("✓ Docs endpoint accessible")
                else:
                    print(f"✗ Docs endpoint failed: {response.status}")
        except Exception as e:
            print(f"✗ Docs endpoint error: {e}")
        
        return True


async def debug_rate_limiter():
    """Debug rate limiting functionality step by step."""
    print("\n=== Rate Limiter Debug ===")
    
    async with aiohttp.ClientSession() as session:
        
        # 1. Test admin endpoints without authentication
        print("\n1. Testing admin endpoints...")
        try:
            async with session.get(f"{API_BASE_URL}/api/v1/admin/rate-limit/config") as response:
                print(f"   Admin config (no auth): {response.status}")
                if response.status == 401:
                    print("   ✓ Authentication required (expected)")
                elif response.status == 200:
                    print("   ⚠ No authentication required (security issue)")
                else:
                    print(f"   ✗ Unexpected status: {response.status}")
        except Exception as e:
            print(f"   ✗ Admin endpoint error: {e}")
        
        # 2. Test admin endpoints with authentication
        print("\n2. Testing admin endpoints with auth...")
        headers = {"Authorization": f"Bearer {ADMIN_TOKEN}"}
        try:
            async with session.get(f"{API_BASE_URL}/api/v1/admin/rate-limit/config", headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    print("   ✓ Admin config accessible")
                    print(f"   Rate limits: {data.get('rate_limits', {})}")
                else:
                    print(f"   ✗ Admin config failed: {response.status}")
                    if response.status == 500:
                        text = await response.text()
                        print(f"   Error details: {text[:200]}...")
        except Exception as e:
            print(f"   ✗ Admin auth error: {e}")
        
        # 3. Test setting user tier
        print("\n3. Testing user tier setting...")
        try:
            url = f"{API_BASE_URL}/api/v1/admin/users/debug_user/tier"
            data = {"user_id": "debug_user", "tier": "free"}
            async with session.post(url, json=data, headers=headers) as response:
                if response.status == 200:
                    result = await response.json()
                    print(f"   ✓ User tier set: {result}")
                else:
                    print(f"   ✗ User tier setting failed: {response.status}")
                    text = await response.text()
                    print(f"   Error details: {text[:200]}...")
        except Exception as e:
            print(f"   ✗ User tier error: {e}")


async def debug_chat_endpoint():
    """Debug the chat endpoint specifically."""
    print("\n=== Chat Endpoint Debug ===")
    
    async with aiohttp.ClientSession() as session:
        
        # 1. Test chat endpoint without user ID
        print("\n1. Testing chat endpoint (anonymous)...")
        try:
            url = f"{API_BASE_URL}/api/v1/chat/chat"
            data = {"message": "Hello, this is a test message"}
            async with session.post(url, json=data) as response:
                print(f"   Status: {response.status}")
                
                # Print response headers
                rate_limit_headers = {k: v for k, v in response.headers.items() 
                                    if k.lower().startswith('x-ratelimit')}
                if rate_limit_headers:
                    print(f"   Rate limit headers: {rate_limit_headers}")
                
                if response.status == 200:
                    print("   ✓ Chat endpoint working")
                elif response.status == 429:
                    print("   ✓ Rate limited (working as expected)")
                    data = await response.json()
                    print(f"   Rate limit info: {data.get('rate_limit', {})}")
                elif response.status == 500:
                    print("   ✗ Internal server error")
                    text = await response.text()
                    print(f"   Error details: {text[:300]}...")
                else:
                    print(f"   ✗ Unexpected status: {response.status}")
                    text = await response.text()
                    print(f"   Response: {text[:200]}...")
                    
        except Exception as e:
            print(f"   ✗ Chat endpoint error: {e}")
        
        # 2. Test with user ID header
        print("\n2. Testing chat endpoint with user ID...")
        try:
            url = f"{API_BASE_URL}/api/v1/chat/chat"
            headers = {"X-User-ID": "debug_user"}
            data = {"message": "Hello with user ID"}
            async with session.post(url, json=data, headers=headers) as response:
                print(f"   Status: {response.status}")
                
                if response.status == 500:
                    text = await response.text()
                    print(f"   Error details: {text[:300]}...")
                    
        except Exception as e:
            print(f"   ✗ Chat with user ID error: {e}")


async def debug_redis_connection():
    """Test Redis connection."""
    print("\n=== Redis Connection Debug ===")
    
    try:
        import redis.asyncio as redis
        
        # Test basic Redis connection
        redis_client = redis.from_url("redis://localhost:6379/0")
        await redis_client.ping()
        print("✓ Redis connection successful")
        
        # Test basic operations
        await redis_client.set("test_key", "test_value")
        value = await redis_client.get("test_key")
        if value and value.decode() == "test_value":
            print("✓ Redis read/write operations working")
        
        await redis_client.delete("test_key")
        await redis_client.close()
        
    except Exception as e:
        print(f"✗ Redis connection failed: {e}")
        print("Make sure Redis is running: docker-compose up redis -d")


async def debug_database_connection():
    """Test database connection."""
    print("\n=== Database Connection Debug ===")
    
    try:
        # This would require importing the database modules
        # For now, just test if the database is accessible via the API
        async with aiohttp.ClientSession() as session:
            # Try an endpoint that would use the database
            async with session.get(f"{API_BASE_URL}/api/v1/articles") as response:
                if response.status == 200:
                    print("✓ Database connection working (via API)")
                elif response.status == 500:
                    print("✗ Database connection issues")
                else:
                    print(f"Database status unclear: {response.status}")
    except Exception as e:
        print(f"✗ Database test error: {e}")


async def main():
    """Run all debug checks."""
    print("Rate Limiter Debug Tool")
    print("=" * 50)
    
    # Check API health first
    if not await debug_api_health():
        print("\n❌ API is not responding. Please check:")
        print("1. Is the API server running? (docker-compose up web)")
        print("2. Is it accessible on http://localhost:8000?")
        print("3. Check the API logs for errors")
        return
    
    # Run other debug checks
    await debug_redis_connection()
    await debug_database_connection()
    await debug_rate_limiter()
    await debug_chat_endpoint()
    
    print("\n" + "=" * 50)
    print("Debug complete. Check the output above for issues.")
    print("\nCommon fixes:")
    print("1. Ensure Redis is running: docker-compose up redis -d")
    print("2. Ensure DB is running: docker-compose up db -d")
    print("3. Check API logs: docker-compose logs web")
    print("4. Restart API: docker-compose restart web")


if __name__ == "__main__":
    asyncio.run(main()) 