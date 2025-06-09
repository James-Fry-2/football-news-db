# fake-useragent Integration Guide

This guide explains how the football news crawler integrates with the [fake-useragent](https://github.com/fake-useragent/fake-useragent) library for robust user-agent rotation and anti-detection capabilities.

## Overview

The enhanced `BaseCrawler` now includes sophisticated user-agent rotation capabilities using real-world browser statistics from the fake-useragent library. This helps avoid detection and blocking by news websites.

## Installation

The fake-useragent library is included in `requirements.txt`:

```bash
pip install -r requirements.txt
```

Or install manually:

```bash
pip install fake-useragent==2.2.0
```

## Features

### 🔄 Automatic Rotation
- User-agents rotate automatically based on configurable intervals
- Uses real-world browser statistics for authenticity
- Supports multiple browsers, platforms, and operating systems

### 🛡️ Anti-Detection
- Varies user-agents to appear as different users/devices
- Supports both desktop and mobile user-agents
- Uses recent browser versions by default

### ⚙️ Highly Configurable
- Choose specific browsers, platforms, and OS types
- Set rotation intervals and minimum browser versions
- Fallback mechanisms for reliability

### 🔧 Seamless Integration
- Works with existing crawler code
- Optional - can be disabled if needed
- Backwards compatible with existing implementations

## Basic Usage

### Default Configuration

```python
from src.crawlers.base_crawler import BaseCrawler

# Enable user-agent rotation with default settings
crawler = BaseCrawler(enable_user_agent_rotation=True)

# The crawler will automatically rotate user-agents every 10 requests
# Uses Chrome, Firefox, Edge, Safari on Windows, Mac, Linux, Android, iOS
```

### Custom Configuration

```python
# Advanced configuration
ua_config = {
    'browsers': ['Chrome', 'Firefox'],        # Only Chrome and Firefox
    'platforms': ['desktop'],                 # Desktop only
    'os': ['Windows', 'Mac OS X'],           # Windows and Mac only
    'min_version': 110.0,                    # Recent versions only
    'rotation_interval': 5,                  # Rotate every 5 requests
    'fallback': 'Custom fallback UA string'
}

crawler = BaseCrawler(
    enable_user_agent_rotation=True,
    ua_config=ua_config
)
```

### Site-Specific Crawlers

```python
from src.crawlers.base_crawler import SiteSpecificCrawler

# BBC crawler with frequent rotation
bbc_crawler = SiteSpecificCrawler(
    'bbc',
    enable_user_agent_rotation=True,
    ua_config={'rotation_interval': 3}  # Rotate every 3 requests
)
```

## Configuration Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `browsers` | List[str] | `['Chrome', 'Firefox', 'Edge', 'Safari']` | Browser types to use |
| `platforms` | List[str] | `['desktop', 'mobile']` | Platform types |
| `os` | List[str] | `['Windows', 'Mac OS X', 'Linux', 'Android', 'iOS']` | Operating systems |
| `min_version` | float | `100.0` | Minimum browser version |
| `rotation_interval` | int | `10` | Requests before rotation |
| `fallback` | str | Chrome 120 UA | Fallback user-agent |

### Available Browser Types
Based on fake-useragent v2.2.0:
- `Chrome`, `Firefox`, `Edge`, `Safari`, `Opera`
- `Google`, `Android`, `Yandex Browser`
- `Samsung Internet`, `Opera Mobile`, `Mobile Safari`
- `Firefox Mobile`, `Firefox iOS`, `Chrome Mobile`
- `Chrome Mobile iOS`, `Edge Mobile`, `DuckDuckGo Mobile`
- `MiuiBrowser`, `Whale`, `Twitter`, `Facebook`, `Amazon Silk`

### Available Platforms
- `desktop` - Desktop/laptop computers
- `mobile` - Mobile phones
- `tablet` - Tablet devices

### Available Operating Systems
- `Windows`, `Linux`, `Ubuntu`, `Chrome OS`
- `Mac OS X`, `Android`, `iOS`

## Monitoring and Debugging

### Check Current Status

```python
# Get detailed information about user-agent setup
info = crawler.get_user_agent_info()

print(f"Rotation enabled: {info['rotation_enabled']}")
print(f"Current UA: {info['current_ua']}")
print(f"Request count: {info['request_count']}")
print(f"Rotation interval: {info['rotation_interval']}")

# Get browser details
if 'ua_details' in info:
    details = info['ua_details']
    print(f"Browser: {details['browser']}")
    print(f"OS: {details['os']}")
    print(f"Usage %: {details['percent']}")
```

### Manual Rotation

```python
# Force a user-agent rotation
new_ua = crawler._get_fresh_user_agent()
crawler.update_headers({'User-Agent': new_ua})
```

## Examples

### News Site Scraping

```python
import asyncio
from src.crawlers.base_crawler import SiteSpecificCrawler

async def scrape_news():
    # Configure for news site scraping
    ua_config = {
        'browsers': ['Chrome', 'Firefox', 'Safari'],
        'platforms': ['desktop', 'mobile'],
        'rotation_interval': 7,  # Change every 7 articles
        'min_version': 115.0     # Very recent browsers
    }
    
    crawler = SiteSpecificCrawler(
        'bbc',
        enable_user_agent_rotation=True,
        ua_config=ua_config
    )
    
    # Scrape articles - user-agent rotates automatically
    for url in article_urls:
        article_data = crawler.extract_article_data(url)
        # Process article...
    
    await crawler.close()

asyncio.run(scrape_news())
```

### Testing Different Configurations

```python
# Test different configurations
configs = [
    {'browsers': ['Chrome'], 'platforms': ['desktop']},
    {'browsers': ['Firefox', 'Safari'], 'platforms': ['mobile']},
    {'browsers': ['Edge'], 'platforms': ['desktop'], 'min_version': 120.0}
]

for i, config in enumerate(configs):
    crawler = BaseCrawler(enable_user_agent_rotation=True, ua_config=config)
    info = crawler.get_user_agent_info()
    print(f"Config {i+1}: {info['current_ua'][:50]}...")
```

## Error Handling

The integration includes robust error handling:

```python
# Automatic fallback if fake-useragent fails
try:
    from fake_useragent import UserAgent
    ua = UserAgent()
    user_agent = ua.random
except Exception:
    # Falls back to default Chrome user-agent
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36..."
```

### Graceful Degradation

- If fake-useragent is not installed, crawlers use static user-agents
- If user-agent generation fails, falls back to default
- Rotation can be disabled without breaking existing code

## Testing

Run the integration test:

```bash
python test_user_agent_integration.py
```

This will:
1. Test basic rotation functionality
2. Verify custom configurations
3. Demonstrate rotation over multiple requests
4. Show site-specific crawler behavior
5. Display detailed user-agent information

## Performance Considerations

### Memory Usage
- User-agent data is loaded once per crawler instance
- Minimal memory overhead (~1-2MB for user-agent database)

### Performance Impact
- User-agent generation: ~0.1ms per request
- Rotation check: ~0.01ms per request
- Negligible impact on overall scraping performance

### Recommendations
- Use rotation intervals of 5-20 requests for balance
- Prefer desktop user-agents for better compatibility
- Use recent browser versions (min_version >= 100.0)

## Best Practices

### 1. Match Site Expectations
```python
# For mobile-first sites
mobile_config = {
    'platforms': ['mobile'],
    'browsers': ['Chrome Mobile', 'Safari Mobile'],
    'rotation_interval': 5
}

# For traditional news sites
desktop_config = {
    'platforms': ['desktop'],
    'browsers': ['Chrome', 'Firefox', 'Edge'],
    'rotation_interval': 10
}
```

### 2. Rate Limiting Integration
```python
import time

async def respectful_scraping(urls):
    crawler = BaseCrawler(enable_user_agent_rotation=True)
    
    for url in urls:
        # Extract with rotation
        data = crawler.extract_article_data(url)
        
        # Be respectful - add delays
        await asyncio.sleep(2)  # 2 second delay between requests
```

### 3. Monitoring Rotation
```python
def log_user_agent_stats(crawler, interval=50):
    if crawler.request_count % interval == 0:
        info = crawler.get_user_agent_info()
        logger.info(f"Requests: {info['request_count']}, "
                   f"Current UA: {info['current_ua'][:50]}...")
```

## Troubleshooting

### Common Issues

1. **ImportError: No module named 'fake_useragent'**
   ```bash
   pip install fake-useragent==2.2.0
   ```

2. **User-agent not rotating**
   - Check if rotation is enabled: `crawler.enable_user_agent_rotation`
   - Verify rotation interval: `crawler.ua_rotation_interval`
   - Check request count: `crawler.request_count`

3. **Same user-agent repeated**
   - Normal behavior - library uses weighted random selection
   - Popular user-agents appear more frequently (realistic)

4. **Site still blocking requests**
   - Add delays between requests
   - Use more conservative rotation intervals
   - Combine with proxy rotation if needed

### Debug Mode

Enable debug logging to see rotation activity:

```python
import logging

logging.getLogger('src.crawlers.base_crawler').setLevel(logging.DEBUG)

# You'll see messages like:
# DEBUG: Generated new user-agent: Mozilla/5.0...
# DEBUG: Rotated user-agent after 10 requests
```

## Integration with Existing Code

The fake-useragent integration is designed to be backwards compatible:

```python
# Existing code continues to work
crawler = BaseCrawler()  # Uses static user-agent

# New code can opt into rotation
crawler = BaseCrawler(enable_user_agent_rotation=True)  # Uses rotation
```

This allows gradual migration and testing without breaking existing functionality. 