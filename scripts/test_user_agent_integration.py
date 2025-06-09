#!/usr/bin/env python3
"""
Test script for fake-useragent integration with BaseCrawler

This script demonstrates how the enhanced BaseCrawler works with user-agent rotation.
Run this after installing fake-useragent to see the integration in action.
"""

import asyncio
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from src.crawlers.base_crawler import BaseCrawler, SiteSpecificCrawler


class TestCrawler(BaseCrawler):
    """Simple test crawler to demonstrate user-agent rotation."""
    
    async def fetch_articles(self):
        """Dummy implementation for testing."""
        return []


async def test_user_agent_rotation():
    """Test user-agent rotation functionality."""
    print("🧪 Testing fake-useragent integration with BaseCrawler\n")
    
    # Test 1: Basic crawler with default settings
    print("📋 Test 1: Basic crawler with default user-agent rotation")
    crawler1 = TestCrawler(enable_user_agent_rotation=True)
    
    info = crawler1.get_user_agent_info()
    print(f"✅ Rotation enabled: {info['rotation_enabled']}")
    print(f"📱 Current UA: {info['current_ua'][:80]}...")
    print(f"🔄 Rotation interval: {info['rotation_interval']}")
    print()
    
    # Test 2: Custom configuration
    print("📋 Test 2: Custom user-agent configuration")
    ua_config = {
        'browsers': ['Chrome', 'Firefox'],
        'platforms': ['desktop'],
        'os': ['Windows', 'Mac OS X'],
        'rotation_interval': 3
    }
    crawler2 = TestCrawler(enable_user_agent_rotation=True, ua_config=ua_config)
    
    info2 = crawler2.get_user_agent_info()
    print(f"✅ Custom config applied: {info2['config']}")
    print(f"📱 Current UA: {info2['current_ua'][:80]}...")
    print()
    
    # Test 3: Simulate multiple requests to trigger rotation
    print("📋 Test 3: Testing user-agent rotation over multiple requests")
    print("Making 10 requests to trigger rotations...")
    
    user_agents_seen = set()
    
    for i in range(10):
        # Simulate a request (this would normally be crawler.extract_article_data())
        crawler2._maybe_rotate_user_agent()
        current_ua = crawler2.headers['User-Agent']
        user_agents_seen.add(current_ua)
        
        if i % 3 == 2:  # Rotation happens every 3 requests
            print(f"🔄 Request {i+1}: UA rotated to: {current_ua[:60]}...")
    
    print(f"📊 Total unique user-agents seen: {len(user_agents_seen)}")
    print()
    
    # Test 4: Site-specific crawler
    print("📋 Test 4: Site-specific crawler with user-agent rotation")
    from src.crawlers.bbc_crawler import BBCCrawler
    
    bbc_crawler = BBCCrawler(enable_user_agent_rotation=True)
    
    bbc_info = bbc_crawler.get_user_agent_info()
    print(f"🌐 BBC crawler UA: {bbc_info['current_ua'][:80]}...")
    print(f"🔄 BBC rotation interval: {bbc_info['rotation_interval']}")
    print()
    
    # Test 5: User-agent details
    print("📋 Test 5: Detailed user-agent information")
    if 'ua_details' in info and info['ua_details']:
        ua_details = info['ua_details']
        print(f"🔍 Browser: {ua_details.get('browser', 'Unknown')}")
        print(f"🖥️  OS: {ua_details.get('os', 'Unknown')}")
        print(f"📊 Usage %: {ua_details.get('percent', 'Unknown')}")
        print(f"📱 Device: {ua_details.get('type', 'Unknown')}")
    
    print("\n✅ All tests completed successfully!")
    
    # Cleanup
    await crawler1.close()
    await crawler2.close()
    await bbc_crawler.close()


def test_without_fake_useragent():
    """Test behavior when fake-useragent is not available."""
    print("🧪 Testing behavior without fake-useragent\n")
    
    # This would be the case if fake-useragent wasn't installed
    crawler = TestCrawler(enable_user_agent_rotation=True)
    
    info = crawler.get_user_agent_info()
    print(f"📋 fake-useragent available: {info['fake_useragent_available']}")
    print(f"🔄 Rotation enabled: {info['rotation_enabled']}")
    print(f"📱 Fallback UA: {info['current_ua'][:80]}...")


if __name__ == "__main__":
    print("🚀 Starting fake-useragent integration tests...\n")
    
    try:
        # Test with fake-useragent
        asyncio.run(test_user_agent_rotation())
    except ImportError:
        print("❌ fake-useragent not installed. Testing fallback behavior...")
        test_without_fake_useragent()
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        sys.exit(1)
    
    print("\n🎉 Integration test completed!") 