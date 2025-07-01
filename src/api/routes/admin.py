from typing import Dict, Optional
from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from loguru import logger

from ..middleware.rate_limiter import (
    set_user_tier, 
    get_user_tier, 
    get_rate_limit_stats,
    RateLimitConfig
)

router = APIRouter()
security = HTTPBearer()

# Pydantic models
class UserTierRequest(BaseModel):
    user_id: str
    tier: str

class UserTierResponse(BaseModel):
    user_id: str
    tier: str
    rate_limit: int

class RateLimitStatsResponse(BaseModel):
    total_requests: int
    blocked_requests: int
    block_rate: float
    requests_by_tier: Dict[str, int]
    blocked_by_tier: Dict[str, int]
    uptime_hours: float


# Simple authentication check (in production, implement proper JWT validation)
async def verify_admin_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify admin authentication token."""
    #TODO: In production, implement proper JWT token validation
    # For now, we'll use a simple token check
    if not credentials.credentials or credentials.credentials != "admin_token_123":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return credentials


@router.get("/rate-limit/stats", response_model=RateLimitStatsResponse)
async def get_rate_limiting_stats(admin: HTTPAuthorizationCredentials = Depends(verify_admin_token)):
    """Get rate limiting statistics."""
    try:
        stats = await get_rate_limit_stats()
        return RateLimitStatsResponse(**stats)
    except Exception as e:
        logger.error(f"Failed to get rate limit stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve rate limit statistics")


@router.get("/rate-limit/config")
async def get_rate_limit_config(admin: HTTPAuthorizationCredentials = Depends(verify_admin_token)):
    """Get current rate limit configuration."""
    return {
        "rate_limits": RateLimitConfig.RATE_LIMITS,
        "window_duration_hours": RateLimitConfig.WINDOW_DURATION // 3600,
        "sub_windows": RateLimitConfig.SUB_WINDOWS,
        "default_tier": RateLimitConfig.DEFAULT_TIER
    }


@router.post("/users/{user_id}/tier", response_model=UserTierResponse)
async def set_user_rate_limit_tier(
    user_id: str,
    tier_request: UserTierRequest,
    admin: HTTPAuthorizationCredentials = Depends(verify_admin_token)
):
    """Set rate limit tier for a specific user."""
    try:
        # Validate tier
        if tier_request.tier not in RateLimitConfig.RATE_LIMITS:
            available_tiers = list(RateLimitConfig.RATE_LIMITS.keys())
            raise HTTPException(
                status_code=400,
                detail=f"Invalid tier '{tier_request.tier}'. Available tiers: {available_tiers}"
            )
        
        # Set user tier
        success = await set_user_tier(user_id, tier_request.tier)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to set user tier")
        
        return UserTierResponse(
            user_id=user_id,
            tier=tier_request.tier,
            rate_limit=RateLimitConfig.RATE_LIMITS[tier_request.tier]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to set user tier for {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to set user tier")


@router.get("/users/{user_id}/tier", response_model=UserTierResponse)
async def get_user_rate_limit_tier(
    user_id: str,
    admin: HTTPAuthorizationCredentials = Depends(verify_admin_token)
):
    """Get rate limit tier for a specific user."""
    try:
        tier = await get_user_tier(user_id)
        return UserTierResponse(
            user_id=user_id,
            tier=tier,
            rate_limit=RateLimitConfig.RATE_LIMITS[tier]
        )
    except Exception as e:
        logger.error(f"Failed to get user tier for {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get user tier")


@router.delete("/users/{user_id}/tier")
async def reset_user_tier(
    user_id: str,
    admin: HTTPAuthorizationCredentials = Depends(verify_admin_token)
):
    """Reset user to default tier."""
    try:
        success = await set_user_tier(user_id, RateLimitConfig.DEFAULT_TIER)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to reset user tier")
        
        return {
            "message": f"User {user_id} reset to default tier '{RateLimitConfig.DEFAULT_TIER}'",
            "tier": RateLimitConfig.DEFAULT_TIER,
            "rate_limit": RateLimitConfig.RATE_LIMITS[RateLimitConfig.DEFAULT_TIER]
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to reset user tier for {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to reset user tier")


@router.get("/users/{user_id}/rate-limit/status")
async def get_user_rate_limit_status(
    user_id: str,
    admin: HTTPAuthorizationCredentials = Depends(verify_admin_token)
):
    """Get current rate limit status for a specific user."""
    try:
        from ..middleware.rate_limiter import SlidingWindowRateLimiter
        from ...config.vector_config import REDIS_URL
        import redis.asyncio as redis
        
        # Create temporary rate limiter to check status
        redis_client = redis.from_url(REDIS_URL)
        rate_limiter = SlidingWindowRateLimiter(redis_client)
        
        try:
            _, rate_limit_info = await rate_limiter.check_rate_limit(user_id)
            return {
                "user_id": user_id,
                "rate_limit_info": rate_limit_info,
                "timestamp": "now"
            }
        finally:
            await redis_client.close()
            
    except Exception as e:
        logger.error(f"Failed to get rate limit status for {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get rate limit status") 