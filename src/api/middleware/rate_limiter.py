# src/api/middleware/rate_limiter.py

import time
import json
import hashlib
from typing import Dict, Optional, Tuple, Callable
from datetime import datetime, timedelta
from collections import defaultdict

import redis.asyncio as redis
from fastapi import Request, Response, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from loguru import logger

from ...config.vector_config import REDIS_URL, REDIS_HOST, REDIS_PORT, REDIS_DB, REDIS_PASSWORD


class RateLimitConfig:
    """Configuration for different user tiers and rate limits."""
    
    # Rate limits per day for different user tiers
    RATE_LIMITS = {
        "free": 50,
        "premium": 500,
        "admin": 10000  # High limit for admin users
    }
    
    # Sliding window duration in seconds (24 hours)
    WINDOW_DURATION = 24 * 60 * 60
    
    # Number of sub-windows for sliding window implementation (1 hour each)
    SUB_WINDOWS = 24
    
    # Sub-window duration in seconds
    SUB_WINDOW_DURATION = WINDOW_DURATION // SUB_WINDOWS
    
    # Redis key prefixes
    RATE_LIMIT_PREFIX = "rate_limit"
    USER_TIER_PREFIX = "user_tier"
    
    # Default tier for unauthenticated users
    DEFAULT_TIER = "free"


class RateLimitStatistics:
    """Track rate limiting statistics."""
    
    def __init__(self):
        self.total_requests = 0
        self.blocked_requests = 0
        self.requests_by_tier = defaultdict(int)
        self.blocked_by_tier = defaultdict(int)
        self.start_time = datetime.now()
    
    def record_request(self, tier: str, blocked: bool = False):
        """Record a request attempt."""
        self.total_requests += 1
        self.requests_by_tier[tier] += 1
        
        if blocked:
            self.blocked_requests += 1
            self.blocked_by_tier[tier] += 1
    
    def get_stats(self) -> Dict:
        """Get comprehensive rate limiting statistics."""
        uptime = datetime.now() - self.start_time
        return {
            "total_requests": self.total_requests,
            "blocked_requests": self.blocked_requests,
            "block_rate": round(self.blocked_requests / max(self.total_requests, 1), 4),
            "requests_by_tier": dict(self.requests_by_tier),
            "blocked_by_tier": dict(self.blocked_by_tier),
            "uptime_hours": round(uptime.total_seconds() / 3600, 2)
        }


class SlidingWindowRateLimiter:
    """Sliding window rate limiter using Redis."""
    
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.config = RateLimitConfig()
        self.stats = RateLimitStatistics()
    
    def _get_current_window_start(self) -> int:
        """Get the start timestamp of the current sub-window."""
        now = int(time.time())
        return now - (now % self.config.SUB_WINDOW_DURATION)
    
    def _get_user_identifier(self, request: Request) -> str:
        """Extract user identifier from request."""
        # Try to get user ID from various sources
        user_id = None
        
        # 1. From JWT token or authorization header
        auth_header = request.headers.get("authorization")
        if auth_header and auth_header.startswith("Bearer "):
            # In a real implementation, you'd decode the JWT here
            # For now, we'll use a simple hash of the token
            token = auth_header[7:]
            user_id = f"user_{hashlib.sha256(token.encode()).hexdigest()[:16]}"
        
        # 2. From query parameter or form data
        if not user_id:
            user_id = request.query_params.get("user_id")
        
        # 3. From custom header
        if not user_id:
            user_id = request.headers.get("x-user-id")
        
        # 4. Fall back to IP address
        if not user_id:
            # Get real IP address considering proxies
            forwarded_for = request.headers.get("x-forwarded-for")
            if forwarded_for:
                user_id = f"ip_{forwarded_for.split(',')[0].strip()}"
            else:
                user_id = f"ip_{request.client.host}"
        
        return user_id
    
    async def get_user_tier(self, user_id: str) -> str:
        """Get user tier from Redis or return default."""
        try:
            tier_key = f"{self.config.USER_TIER_PREFIX}:{user_id}"
            tier = await self.redis.get(tier_key)
            return tier.decode() if tier else self.config.DEFAULT_TIER
        except Exception as e:
            logger.warning(f"Failed to get user tier for {user_id}: {e}")
            return self.config.DEFAULT_TIER
    
    async def set_user_tier(self, user_id: str, tier: str) -> bool:
        """Set user tier in Redis."""
        try:
            if tier not in self.config.RATE_LIMITS:
                raise ValueError(f"Invalid tier: {tier}")
            
            tier_key = f"{self.config.USER_TIER_PREFIX}:{user_id}"
            await self.redis.set(tier_key, tier)
            logger.info(f"Set user {user_id} to tier {tier}")
            return True
        except Exception as e:
            logger.error(f"Failed to set user tier for {user_id}: {e}")
            return False
    
    async def _cleanup_old_windows(self, base_key: str) -> None:
        """Remove old sub-window data to prevent memory leaks."""
        try:
            current_window = self._get_current_window_start()
            cutoff_time = current_window - self.config.WINDOW_DURATION
            
            # Get all hash fields (sub-window timestamps)
            fields = await self.redis.hkeys(base_key)
            
            # Remove fields older than the sliding window
            for field in fields:
                window_time = int(field.decode())
                if window_time < cutoff_time:
                    await self.redis.hdel(base_key, field)
                    
        except Exception as e:
            logger.warning(f"Failed to cleanup old windows for {base_key}: {e}")
    
    async def check_rate_limit(self, user_id: str) -> Tuple[bool, Dict]:
        """
        Check if user is within rate limit using sliding window.
        
        Returns:
            Tuple of (is_allowed, rate_limit_info)
        """
        tier = await self.get_user_tier(user_id)
        rate_limit = self.config.RATE_LIMITS[tier]
        
        current_window = self._get_current_window_start()
        base_key = f"{self.config.RATE_LIMIT_PREFIX}:{user_id}"
        
        try:
            # Cleanup old windows first
            await self._cleanup_old_windows(base_key)
            
            # Get all request counts within the sliding window
            window_start = current_window - self.config.WINDOW_DURATION + self.config.SUB_WINDOW_DURATION
            total_requests = 0
            
            # Count requests in all sub-windows within the sliding window
            for i in range(self.config.SUB_WINDOWS):
                window_timestamp = window_start + (i * self.config.SUB_WINDOW_DURATION)
                count = await self.redis.hget(base_key, str(window_timestamp))
                if count:
                    total_requests += int(count)
            
            # Check if within limit
            is_allowed = total_requests < rate_limit
            
            if is_allowed:
                # Increment counter for current window
                await self.redis.hincrby(base_key, str(current_window), 1)
                # Set expiration for the hash key (window duration + buffer)
                await self.redis.expire(base_key, self.config.WINDOW_DURATION + 3600)
            
            # Calculate time until limit resets (next sub-window)
            next_window = current_window + self.config.SUB_WINDOW_DURATION
            reset_time = next_window
            
            rate_limit_info = {
                "allowed": is_allowed,
                "tier": tier,
                "limit": rate_limit,
                "current_usage": total_requests + (1 if is_allowed else 0),
                "remaining": max(0, rate_limit - total_requests - (1 if is_allowed else 0)),
                "reset_time": reset_time,
                "reset_in_seconds": max(0, reset_time - int(time.time())),
                "window_duration": self.config.WINDOW_DURATION
            }
            
            # Record statistics
            self.stats.record_request(tier, not is_allowed)
            
            return is_allowed, rate_limit_info
            
        except Exception as e:
            logger.error(f"Rate limit check failed for {user_id}: {e}")
            # In case of Redis errors, allow the request but log the issue
            return True, {
                "allowed": True,
                "error": "Rate limit check failed",
                "tier": tier,
                "limit": rate_limit
            }
    
    def get_statistics(self) -> Dict:
        """Get rate limiting statistics."""
        return self.stats.get_stats()


class RateLimitMiddleware(BaseHTTPMiddleware):
    """FastAPI middleware for rate limiting chat requests."""
    
    def __init__(self, app, redis_url: str = None, exclude_paths: list = None):
        super().__init__(app)
        
        # Initialize Redis connection
        self.redis_url = redis_url or REDIS_URL
        self.redis_client = None
        self.rate_limiter = None
        
        # Paths to exclude from rate limiting
        self.exclude_paths = exclude_paths or [
            "/health",
            "/docs",
            "/openapi.json",
            "/api/v1/chat/stats",  # Rate limit stats endpoint
            "/api/v1/admin"  # Admin endpoints
        ]
        
        # Chat-specific paths to rate limit
        self.chat_paths = [
            "/api/v1/chat/chat",
            "/api/v1/chat/stream",
            "/ws/chat"
        ]
    
    async def _init_redis(self):
        """Initialize Redis connection if not already done."""
        if self.redis_client is None:
            try:
                # Debug logging
                logger.info(f"Attempting to connect to Redis with URL: {self.redis_url}")
                logger.info(f"Redis host: {REDIS_HOST}, port: {REDIS_PORT}, db: {REDIS_DB}")
                
                # Parse Redis URL or use individual components
                if self.redis_url and self.redis_url.startswith("redis://"):
                    logger.info(f"Using Redis URL: {self.redis_url}")
                    self.redis_client = redis.from_url(
                        self.redis_url,
                        decode_responses=False,
                        retry_on_timeout=True,
                        health_check_interval=30
                    )
                else:
                    logger.info(f"Using Redis host/port: {REDIS_HOST}:{REDIS_PORT}")
                    self.redis_client = redis.Redis(
                        host=REDIS_HOST,
                        port=REDIS_PORT,
                        db=REDIS_DB,
                        password=REDIS_PASSWORD if REDIS_PASSWORD else None,
                        decode_responses=False,
                        retry_on_timeout=True,
                        health_check_interval=30
                    )
                
                # Test connection
                await self.redis_client.ping()
                self.rate_limiter = SlidingWindowRateLimiter(self.redis_client)
                logger.info("Rate limiter initialized with Redis connection")
                
            except Exception as e:
                logger.error(f"Failed to initialize Redis for rate limiting: {e}")
                logger.error(f"Redis URL being used: {self.redis_url}")
                logger.error(f"Redis config - Host: {REDIS_HOST}, Port: {REDIS_PORT}, DB: {REDIS_DB}")
                # Rate limiting will be disabled if Redis fails
                self.redis_client = None
                self.rate_limiter = None
    
    def _should_rate_limit(self, request: Request) -> bool:
        """Determine if the request should be rate limited."""
        path = request.url.path
        
        # Exclude certain paths
        for exclude_path in self.exclude_paths:
            if path.startswith(exclude_path):
                return False
        
        # Only rate limit chat endpoints
        for chat_path in self.chat_paths:
            if path.startswith(chat_path):
                return True
        
        # Don't rate limit other endpoints
        return False
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with rate limiting."""
        
        # Initialize Redis connection if needed
        await self._init_redis()
        
        # Skip rate limiting if not applicable
        if not self._should_rate_limit(request) or not self.rate_limiter:
            return await call_next(request)
        
        # Get user identifier and check rate limit
        user_id = self.rate_limiter._get_user_identifier(request)
        is_allowed, rate_limit_info = await self.rate_limiter.check_rate_limit(user_id)
        
        if not is_allowed:
            # Rate limit exceeded
            logger.warning(f"Rate limit exceeded for user {user_id}: {rate_limit_info}")
            
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Rate limit exceeded",
                    "message": f"You have exceeded your rate limit of {rate_limit_info['limit']} requests per day for {rate_limit_info['tier']} tier",
                    "rate_limit": rate_limit_info,
                    "retry_after": rate_limit_info.get("reset_in_seconds", 3600)
                },
                headers={
                    "X-RateLimit-Limit": str(rate_limit_info["limit"]),
                    "X-RateLimit-Remaining": str(rate_limit_info["remaining"]),
                    "X-RateLimit-Reset": str(rate_limit_info["reset_time"]),
                    "X-RateLimit-Tier": rate_limit_info["tier"],
                    "Retry-After": str(rate_limit_info.get("reset_in_seconds", 3600))
                }
            )
        
        # Process the request
        response = await call_next(request)
        
        # Add rate limit headers to successful responses
        if hasattr(response, "headers"):
            response.headers["X-RateLimit-Limit"] = str(rate_limit_info["limit"])
            response.headers["X-RateLimit-Remaining"] = str(rate_limit_info["remaining"])
            response.headers["X-RateLimit-Reset"] = str(rate_limit_info["reset_time"])
            response.headers["X-RateLimit-Tier"] = rate_limit_info["tier"]
        
        return response


# Utility functions for managing user tiers
async def set_user_tier(user_id: str, tier: str, redis_url: str = None) -> bool:
    """Utility function to set user tier."""
    redis_client = None
    try:
        redis_url = redis_url or REDIS_URL
        redis_client = redis.from_url(redis_url)
        rate_limiter = SlidingWindowRateLimiter(redis_client)
        return await rate_limiter.set_user_tier(user_id, tier)
    except Exception as e:
        logger.error(f"Failed to set user tier: {e}")
        return False
    finally:
        if redis_client:
            await redis_client.close()


async def get_user_tier(user_id: str, redis_url: str = None) -> str:
    """Utility function to get user tier."""
    redis_client = None
    try:
        redis_url = redis_url or REDIS_URL
        redis_client = redis.from_url(redis_url)
        rate_limiter = SlidingWindowRateLimiter(redis_client)
        return await rate_limiter.get_user_tier(user_id)
    except Exception as e:
        logger.error(f"Failed to get user tier: {e}")
        return RateLimitConfig.DEFAULT_TIER
    finally:
        if redis_client:
            await redis_client.close()


async def get_rate_limit_stats(redis_url: str = None) -> Dict:
    """Utility function to get rate limiting statistics."""
    redis_client = None
    try:
        redis_url = redis_url or REDIS_URL
        redis_client = redis.from_url(redis_url)
        rate_limiter = SlidingWindowRateLimiter(redis_client)
        return rate_limiter.get_statistics()
    except Exception as e:
        logger.error(f"Failed to get rate limit stats: {e}")
        return {"error": str(e)}
    finally:
        if redis_client:
            await redis_client.close() 