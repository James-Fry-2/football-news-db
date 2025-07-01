#!/usr/bin/env python3
# scripts/test_rate_limiter.py

import asyncio
import aiohttp
import json
import time
from typing import Dict, List
from datetime import datetime

# Configuration
API_BASE_URL = "http://localhost:8000"
ADMIN_TOKEN = "admin_token_123"  # In production, use proper JWT tokens


async def test_rate_limiting():
    """Test the rate limiting functionality."""
    print("=== Testing Rate Limiting Functionality ===\n")
    
    # Test user configurations
    test_users = [
        {"user_id": "test_free_user", "tier": "free", "expected_limit": 50},
        {"user_id": "test_premium_user", "tier": "premium", "expected_limit": 500}
    ]
    
    async with aiohttp.ClientSession() as session:
        
        # 1. Set up test users
        print("1. Setting up test users...")
        for user in test_users:
            await set_user_tier(session, user["user_id"], user["tier"])
            print(f"   ✓ Set {user['user_id']} to {user['tier']} tier")
        
        print()
        
        # 2. Test rate limiting for free user
        print("2. Testing rate limiting for free user...")
        await test_user_rate_limits(session, "test_free_user", max_requests=55)  # Exceed limit
        
        print()
        
        # 3. Test rate limiting for premium user  
        print("3. Testing rate limiting for premium user...")
        await test_user_rate_limits(session, "test_premium_user", max_requests=10)  # Within limit
        
        print()
        
        # 4. Test IP-based rate limiting (no user ID)
        print("4. Testing IP-based rate limiting...")
        await test_anonymous_rate_limits(session, max_requests=55)
        
        print()
        
        # 5. Get statistics
        print("5. Getting rate limiting statistics...")
        await get_rate_limit_stats(session)
        
        print()
        
        # 6. Test admin endpoints
        print("6. Testing admin endpoints...")
        await test_admin_endpoints(session)


async def set_user_tier(session: aiohttp.ClientSession, user_id: str, tier: str):
    """Set user tier using admin endpoint."""
    url = f"{API_BASE_URL}/api/v1/admin/users/{user_id}/tier"
    headers = {"Authorization": f"Bearer {ADMIN_TOKEN}"}
    data = {"user_id": user_id, "tier": tier}
    
    async with session.post(url, json=data, headers=headers) as response:
        if response.status == 200:
            result = await response.json()
            return result
        else:
            print(f"   ✗ Failed to set user tier: {response.status}")
            return None


async def test_user_rate_limits(session: aiohttp.ClientSession, user_id: str, max_requests: int = 55):
    """Test rate limiting for a specific user."""
    print(f"   Testing {max_requests} requests for user: {user_id}")
    
    successful_requests = 0
    blocked_requests = 0
    
    # Make requests
    for i in range(max_requests):
        success = await make_chat_request(session, user_id, f"Test message {i+1}")
        if success:
            successful_requests += 1
        else:
            blocked_requests += 1
        
        # Show progress every 10 requests
        if (i + 1) % 10 == 0:
            print(f"   Progress: {i+1}/{max_requests} requests sent")
    
    print(f"   Results: {successful_requests} successful, {blocked_requests} blocked")


async def test_anonymous_rate_limits(session: aiohttp.ClientSession, max_requests: int = 55):
    """Test rate limiting for anonymous users (IP-based)."""
    print(f"   Testing {max_requests} anonymous requests")
    
    successful_requests = 0
    blocked_requests = 0
    
    # Make requests without user ID
    for i in range(max_requests):
        success = await make_chat_request(session, None, f"Anonymous message {i+1}")
        if success:
            successful_requests += 1
        else:
            blocked_requests += 1
        
        # Show progress every 10 requests
        if (i + 1) % 10 == 0:
            print(f"   Progress: {i+1}/{max_requests} requests sent")
    
    print(f"   Results: {successful_requests} successful, {blocked_requests} blocked")


async def make_chat_request(session: aiohttp.ClientSession, user_id: str = None, message: str = "Test") -> bool:
    """Make a chat request and return True if successful, False if rate limited."""
    url = f"{API_BASE_URL}/api/v1/chat/chat"
    headers = {}
    
    # Add user ID to headers if provided
    if user_id:
        headers["X-User-ID"] = user_id
    
    data = {
        "message": message,
        "conversation_id": "test_conversation"
    }
    
    try:
        async with session.post(url, json=data, headers=headers) as response:
            if response.status == 200:
                return True
            elif response.status == 429:
                # Rate limited
                return False
            else:
                print(f"   Unexpected status code: {response.status}")
                return False
    except Exception as e:
        print(f"   Request error: {e}")
        return False


async def get_rate_limit_stats(session: aiohttp.ClientSession):
    """Get and display rate limiting statistics."""
    url = f"{API_BASE_URL}/api/v1/chat/stats"
    
    try:
        async with session.get(url) as response:
            if response.status == 200:
                stats = await response.json()
                print("   Rate Limiting Statistics:")
                print(f"   - Total requests: {stats['rate_limiting'].get('total_requests', 0)}")
                print(f"   - Blocked requests: {stats['rate_limiting'].get('blocked_requests', 0)}")
                print(f"   - Block rate: {stats['rate_limiting'].get('block_rate', 0):.2%}")
                print(f"   - Requests by tier: {stats['rate_limiting'].get('requests_by_tier', {})}")
                print(f"   - Blocked by tier: {stats['rate_limiting'].get('blocked_by_tier', {})}")
            else:
                print(f"   Failed to get stats: {response.status}")
    except Exception as e:
        print(f"   Error getting stats: {e}")


async def test_admin_endpoints(session: aiohttp.ClientSession):
    """Test admin endpoints."""
    headers = {"Authorization": f"Bearer {ADMIN_TOKEN}"}
    
    # Test get rate limit config
    url = f"{API_BASE_URL}/api/v1/admin/rate-limit/config"
    async with session.get(url, headers=headers) as response:
        if response.status == 200:
            config = await response.json()
            print("   ✓ Rate limit config retrieved")
            print(f"     Tiers: {config['rate_limits']}")
        else:
            print(f"   ✗ Failed to get config: {response.status}")
    
    # Test get user tier
    url = f"{API_BASE_URL}/api/v1/admin/users/test_free_user/tier"
    async with session.get(url, headers=headers) as response:
        if response.status == 200:
            user_info = await response.json()
            print(f"   ✓ User tier info: {user_info}")
        else:
            print(f"   ✗ Failed to get user tier: {response.status}")


async def main():
    """Main test function."""
    print("Starting rate limiter tests...")
    print("Make sure the API server is running on http://localhost:8000")
    print()
    
    try:
        await test_rate_limiting()
        print("\n=== Tests completed ===")
    except Exception as e:
        print(f"\nTest failed with error: {e}")


if __name__ == "__main__":
    asyncio.run(main()) 