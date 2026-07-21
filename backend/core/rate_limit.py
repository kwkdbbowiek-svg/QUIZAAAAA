"""
Rate Limiting — DDoS, Brute Force, Bot himoyasi
"""

from fastapi import Request, HTTPException, status
from shared.database.redis_client import get_redis
import logging

logger = logging.getLogger(__name__)


async def rate_limit(request: Request, limit: int = 60, window: int = 60):
    """
    Global rate limiter — har bir IP uchun.
    limit: window soniya ichida max so'rovlar soni
    window: soniyada oyna
    """
    redis = await get_redis()
    ip = request.client.host if request.client else "unknown"
    path = request.url.path
    key = f"ratelimit:{ip}:{path}"

    try:
        count = await redis.incr(key)
        if count == 1:
            await redis.expire(key, window)
        if count > limit:
            logger.warning(f"Rate limit exceeded: {ip} -> {path}")
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Juda ko'p so'rov. Biroz kutib turing.",
                headers={"Retry-After": str(window)},
            )
    except HTTPException:
        raise
    except Exception:
        pass  # Redis muammosi bo'lsa o'tkazib yuboramiz


async def auth_rate_limit(request: Request):
    """Login uchun qattiqroq limit — Brute Force himoyasi"""
    await rate_limit(request, limit=5, window=60)


async def api_rate_limit(request: Request):
    """API uchun umumiy limit"""
    await rate_limit(request, limit=100, window=60)
