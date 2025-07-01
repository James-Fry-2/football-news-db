# Rate Limiting Scripts

This directory contains utility scripts for managing the rate limiting system.

## Available Scripts

### 1. `manage_rate_limits.py`
Command-line tool for managing user rate limit tiers.

#### Usage Examples:

```bash
# List available tiers
python scripts/manage_rate_limits.py list-tiers

# Set a user to premium tier
python scripts/manage_rate_limits.py set-tier user123 premium

# Get current tier for a user  
python scripts/manage_rate_limits.py get-tier user123

# View rate limiting statistics
python scripts/manage_rate_limits.py stats

# Set multiple users to same tier
python scripts/manage_rate_limits.py batch-set premium user1 user2 user3
```

### 2. `test_rate_limiter.py`
Comprehensive test script for rate limiting functionality.

#### Usage:
```bash
# Make sure API server is running first
python scripts/test_rate_limiter.py
```

This script will:
- Set up test users with different tiers
- Test rate limiting for free users (50/day limit)
- Test rate limiting for premium users (500/day limit)  
- Test anonymous IP-based rate limiting
- Display statistics and admin endpoint functionality

## Prerequisites

1. **Redis Server**: Must be running and accessible
2. **API Server**: Must be running on localhost:8000
3. **Environment**: Proper `.env` configuration

## Quick Setup

1. Start Redis:
```bash
docker-compose up redis -d
```

2. Start API server:
```bash
python -m src.api.app
```

3. Run tests:
```bash
python scripts/test_rate_limiter.py
```

## Troubleshooting

### Redis Connection Issues
```bash
# Check Redis status
docker-compose ps redis

# Check Redis logs
docker-compose logs redis

# Test Redis connectivity
redis-cli ping
```

### Permission Issues
Make scripts executable:
```bash
chmod +x scripts/manage_rate_limits.py
chmod +x scripts/test_rate_limiter.py
```

### Import Errors
Ensure you're running from the project root:
```bash
cd /path/to/football-news-db
python scripts/manage_rate_limits.py
``` 