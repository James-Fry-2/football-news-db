# Rate Limiting System

## Overview

The Football News DB API implements a comprehensive rate limiting system using Redis for tracking request counts and a sliding window algorithm to ensure fair usage across different user tiers.

## Features

- **Sliding Window Rate Limiting**: More accurate than fixed windows
- **Multi-tier Support**: Different limits for free, premium, and admin users
- **Redis-based Tracking**: Distributed and persistent rate limit counters
- **IP-based Fallback**: Rate limiting works even for anonymous users
- **Real-time Statistics**: Monitor rate limiting performance
- **Admin Management**: Full API for managing user tiers and limits

## Rate Limits

| User Tier | Requests per Day | Description |
|-----------|------------------|-------------|
| Free      | 50               | Default tier for anonymous/free users |
| Premium   | 500              | Paid subscription tier |
| Admin     | 10,000           | Administrative access |

## Technical Implementation

### Sliding Window Algorithm

The system uses a sliding window approach with 24 sub-windows (1 hour each) to provide smooth rate limiting:

- **Window Duration**: 24 hours
- **Sub-windows**: 24 (1 hour each)
- **Granularity**: Requests are counted per hour
- **Memory Efficiency**: Old sub-windows are automatically cleaned up

### User Identification

Users are identified in the following priority order:

1. **JWT Token**: From `Authorization: Bearer <token>` header
2. **User ID**: From `X-User-ID` header or query parameter
3. **IP Address**: Fallback for anonymous users (considers X-Forwarded-For)

### Redis Storage

Rate limit data is stored in Redis with the following structure:

```
rate_limit:<user_id> -> Hash {
  <timestamp1>: <count1>,
  <timestamp2>: <count2>,
  ...
}

user_tier:<user_id> -> <tier_name>
```

## API Endpoints

### Protected Endpoints

Rate limiting is applied to these chat endpoints:

- `POST /api/v1/chat/chat`
- `GET /api/v1/chat/stream`
- `WebSocket /ws/chat/*`

### Admin Endpoints

#### Set User Tier
```http
POST /api/v1/admin/users/{user_id}/tier
Authorization: Bearer <admin_token>
Content-Type: application/json

{
  "user_id": "user123",
  "tier": "premium"
}
```

#### Get User Tier
```http
GET /api/v1/admin/users/{user_id}/tier
Authorization: Bearer <admin_token>
```

#### Get Rate Limit Configuration
```http
GET /api/v1/admin/rate-limit/config
Authorization: Bearer <admin_token>
```

#### Get Rate Limit Statistics
```http
GET /api/v1/admin/rate-limit/stats
Authorization: Bearer <admin_token>
```

#### Get User Rate Limit Status
```http
GET /api/v1/admin/users/{user_id}/rate-limit/status
Authorization: Bearer <admin_token>
```

### Public Endpoints

#### Get Chat Statistics
```http
GET /api/v1/chat/stats
```

Returns both rate limiting and LLM cache statistics.

## Response Headers

All responses to rate-limited endpoints include these headers:

```http
X-RateLimit-Limit: 50
X-RateLimit-Remaining: 23
X-RateLimit-Reset: 1640995200
X-RateLimit-Tier: free
```

When rate limited (HTTP 429):

```http
HTTP/1.1 429 Too Many Requests
Retry-After: 3600
X-RateLimit-Limit: 50
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1640995200
X-RateLimit-Tier: free

{
  "error": "Rate limit exceeded",
  "message": "You have exceeded your rate limit of 50 requests per day for free tier",
  "rate_limit": {
    "allowed": false,
    "tier": "free",
    "limit": 50,
    "current_usage": 51,
    "remaining": 0,
    "reset_time": 1640995200,
    "reset_in_seconds": 3600,
    "window_duration": 86400
  },
  "retry_after": 3600
}
```

## Configuration

### Environment Variables

Add these to your `.env` file:

```bash
# Redis Configuration
REDIS_URL=redis://redis:6379/0
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=

# Optional: Customize rate limits (not yet implemented)
RATE_LIMIT_FREE=50
RATE_LIMIT_PREMIUM=500
RATE_LIMIT_ADMIN=10000
```

### Docker Setup

The system is designed to work with the existing Docker Compose setup. Redis is already included:

```yaml
services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    networks:
      - app-network
```

## Usage Examples

### Setting User Tiers (Admin)

```python
import aiohttp

async def set_user_tier(user_id: str, tier: str):
    async with aiohttp.ClientSession() as session:
        url = "http://localhost:8000/api/v1/admin/users/{user_id}/tier"
        headers = {"Authorization": "Bearer admin_token_123"}
        data = {"user_id": user_id, "tier": tier}
        
        async with session.post(url, json=data, headers=headers) as response:
            return await response.json()

# Set user to premium tier
await set_user_tier("user123", "premium")
```

### Making Requests with User ID

```python
import aiohttp

async def make_chat_request(user_id: str, message: str):
    async with aiohttp.ClientSession() as session:
        url = "http://localhost:8000/api/v1/chat/chat"
        headers = {"X-User-ID": user_id}
        data = {"message": message}
        
        async with session.post(url, json=data, headers=headers) as response:
            if response.status == 429:
                print("Rate limited!")
                return None
            return await response.json()

# Make request as specific user
response = await make_chat_request("user123", "What's the latest football news?")
```

### Checking Rate Limit Status

```javascript
// Frontend JavaScript example
fetch('/api/v1/chat/chat', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'X-User-ID': 'user123'
  },
  body: JSON.stringify({
    message: 'Hello'
  })
})
.then(response => {
  // Check rate limit headers
  const limit = response.headers.get('X-RateLimit-Limit');
  const remaining = response.headers.get('X-RateLimit-Remaining');
  const tier = response.headers.get('X-RateLimit-Tier');
  
  console.log(`Rate limit: ${remaining}/${limit} (${tier} tier)`);
  
  if (response.status === 429) {
    const retryAfter = response.headers.get('Retry-After');
    console.log(`Rate limited. Retry after ${retryAfter} seconds`);
  }
  
  return response.json();
});
```

## Testing

### Manual Testing

1. Start the API server with Redis:
```bash
docker-compose up redis
python -m src.api.app
```

2. Run the test script:
```bash
python scripts/test_rate_limiter.py
```

### Unit Testing

```python
import pytest
from src.api.middleware.rate_limiter import SlidingWindowRateLimiter

@pytest.mark.asyncio
async def test_rate_limiting():
    # Mock Redis client
    redis_client = MockRedisClient()
    limiter = SlidingWindowRateLimiter(redis_client)
    
    # Test within limits
    allowed, info = await limiter.check_rate_limit("test_user")
    assert allowed == True
    assert info["remaining"] == 49
```

## Monitoring

### Metrics to Track

- **Request Volume**: Total requests per tier
- **Block Rate**: Percentage of requests blocked
- **User Distribution**: Users per tier
- **Response Times**: Impact on API performance

### Alerting

Consider setting up alerts for:

- High block rates (>10%)
- Redis connection failures
- Unusual traffic patterns

## Security Considerations

### Admin Authentication

The current implementation uses a simple token for admin endpoints. In production:

1. Implement proper JWT authentication
2. Use role-based access control (RBAC)
3. Audit admin actions

### Rate Limit Bypass

To prevent abuse:

1. Monitor for rapid user switching
2. Implement IP-based secondary limits
3. Log suspicious patterns

### Redis Security

1. Use Redis AUTH (password)
2. Configure Redis to bind to specific interfaces
3. Use Redis TLS in production
4. Regular backup of Redis data

## Troubleshooting

### Common Issues

#### Redis Connection Failed
```
Error: Failed to initialize Redis for rate limiting
```
**Solution**: Check Redis server status and connection details.

#### Rate Limits Not Working
```
All requests are allowed despite limits
```
**Solution**: Verify middleware is properly registered before CORS middleware.

#### High Memory Usage
```
Redis memory increasing over time
```
**Solution**: Old sub-windows should auto-cleanup. Check cleanup function.

### Debug Commands

```bash
# Check Redis connection
redis-cli ping

# View rate limit data
redis-cli keys "rate_limit:*"
redis-cli hgetall "rate_limit:user123"

# View user tiers
redis-cli keys "user_tier:*"
redis-cli get "user_tier:user123"
```

## Performance

### Benchmarks

Expected performance characteristics:

- **Throughput**: 1000+ requests/second
- **Latency Impact**: <5ms per request
- **Memory Usage**: ~100 bytes per active user
- **Redis Operations**: 2-3 per request (read, increment, cleanup)

### Optimization Tips

1. **Connection Pooling**: Use Redis connection pooling
2. **Batch Operations**: Group Redis operations when possible
3. **Monitoring**: Track performance metrics
4. **Scaling**: Consider Redis Cluster for high volume

## Future Enhancements

1. **Dynamic Limits**: Configure limits without code changes
2. **Geographic Limits**: Different limits per region
3. **Burst Allowance**: Allow temporary bursts above limits
4. **User Notifications**: Warn users approaching limits
5. **Analytics Dashboard**: Web UI for monitoring
6. **API Rate Limiting**: Extend to other endpoint types 