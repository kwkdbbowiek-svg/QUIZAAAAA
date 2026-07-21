"""
Redis client - keshlash, real-time reyting va sessiyalar uchun
"""

import json
import redis.asyncio as aioredis
from typing import Optional, Any
from shared.config import settings
import logging

logger = logging.getLogger(__name__)

# Global Redis instance
_redis_client: Optional[aioredis.Redis] = None


async def get_redis() -> aioredis.Redis:
    """Redis client singleton"""
    global _redis_client
    if _redis_client is None:
        _redis_client = aioredis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
            max_connections=20,
        )
    return _redis_client


async def close_redis():
    """Redis ulanishini yopish"""
    global _redis_client
    if _redis_client:
        await _redis_client.close()
        _redis_client = None


# ─── Reyting Xizmati ─────────────────────────────────────────────────────────

class RatingService:
    """Redis Sorted Sets yordamida real-time reyting"""

    def __init__(self, redis: aioredis.Redis):
        self.redis = redis
        self.daily_key = settings.DAILY_RATING_KEY
        self.weekly_key = settings.WEEKLY_RATING_KEY
        self.global_key = settings.GLOBAL_RATING_KEY

    async def update_score(self, user_id: int, xp_gained: int):
        """Foydalanuvchi scoreni yangilash"""
        pipe = self.redis.pipeline()
        pipe.zincrby(self.daily_key, xp_gained, str(user_id))
        pipe.zincrby(self.weekly_key, xp_gained, str(user_id))
        pipe.zincrby(self.global_key, xp_gained, str(user_id))
        await pipe.execute()

    async def get_user_ranks(self, user_id: int) -> dict:
        """Foydalanuvchining barcha reyting o'rinlarini olish"""
        pipe = self.redis.pipeline()
        pipe.zrevrank(self.daily_key, str(user_id))
        pipe.zrevrank(self.weekly_key, str(user_id))
        pipe.zrevrank(self.global_key, str(user_id))
        pipe.zscore(self.daily_key, str(user_id))
        pipe.zscore(self.weekly_key, str(user_id))
        pipe.zscore(self.global_key, str(user_id))
        results = await pipe.execute()

        return {
            "daily_rank": (results[0] + 1) if results[0] is not None else None,
            "weekly_rank": (results[1] + 1) if results[1] is not None else None,
            "global_rank": (results[2] + 1) if results[2] is not None else None,
            "daily_score": int(results[3] or 0),
            "weekly_score": int(results[4] or 0),
            "global_score": int(results[5] or 0),
        }

    async def get_top_users(self, board_type: str = "global", limit: int = 10) -> list:
        """Top foydalanuvchilarni olish"""
        key_map = {
            "daily": self.daily_key,
            "weekly": self.weekly_key,
            "global": self.global_key,
        }
        key = key_map.get(board_type, self.global_key)
        results = await self.redis.zrevrange(key, 0, limit - 1, withscores=True)
        return [{"user_id": int(uid), "score": int(score)} for uid, score in results]

    async def reset_daily(self):
        """Kunlik reytingni reset qilish"""
        await self.redis.delete(self.daily_key)

    async def reset_weekly(self):
        """Haftalik reytingni reset qilish"""
        await self.redis.delete(self.weekly_key)


# ─── Kesh Xizmati ─────────────────────────────────────────────────────────────

class CacheService:
    """Umumiy keshlash xizmati"""

    def __init__(self, redis: aioredis.Redis):
        self.redis = redis

    async def set(self, key: str, value: Any, expire: int = 300):
        """Keshga yozish"""
        await self.redis.set(key, json.dumps(value), ex=expire)

    async def get(self, key: str) -> Optional[Any]:
        """Keshdan o'qish"""
        data = await self.redis.get(key)
        if data:
            return json.loads(data)
        return None

    async def delete(self, key: str):
        """Keshdan o'chirish"""
        await self.redis.delete(key)

    async def exists(self, key: str) -> bool:
        """Kesh mavjudligini tekshirish"""
        return bool(await self.redis.exists(key))

    async def set_session(self, user_id: int, data: dict, expire: int = 86400):
        """Foydalanuvchi sessiyasini saqlash (1 kun)"""
        key = f"session:{user_id}"
        await self.redis.set(key, json.dumps(data), ex=expire)

    async def get_session(self, user_id: int) -> Optional[dict]:
        """Foydalanuvchi sessiyasini olish"""
        key = f"session:{user_id}"
        data = await self.redis.get(key)
        if data:
            return json.loads(data)
        return None

    async def delete_session(self, user_id: int):
        """Sessiyani o'chirish"""
        await self.redis.delete(f"session:{user_id}")

    async def set_quiz_state(self, user_id: int, state: dict, expire: int = 3600):
        """Quiz holatini saqlash"""
        key = f"quiz_state:{user_id}"
        await self.redis.set(key, json.dumps(state), ex=expire)

    async def get_quiz_state(self, user_id: int) -> Optional[dict]:
        """Quiz holatini olish"""
        key = f"quiz_state:{user_id}"
        data = await self.redis.get(key)
        if data:
            return json.loads(data)
        return None

    async def delete_quiz_state(self, user_id: int):
        """Quiz holatini o'chirish"""
        await self.redis.delete(f"quiz_state:{user_id}")


# ─── Rate Limiter ─────────────────────────────────────────────────────────────

class RateLimiter:
    """So'rovlar chastotasini cheklash"""

    def __init__(self, redis: aioredis.Redis):
        self.redis = redis

    async def is_allowed(self, key: str, limit: int, window: int = 60) -> bool:
        """
        So'rov ruxsatli yoki yo'qligini tekshirish
        key: unikal kalit (masalan, user_id)
        limit: oyna ichida ruxsat etilgan so'rovlar soni
        window: oyna vaqti (sekundda)
        """
        pipe = self.redis.pipeline()
        rate_key = f"ratelimit:{key}"
        pipe.incr(rate_key)
        pipe.expire(rate_key, window)
        results = await pipe.execute()
        count = results[0]
        return count <= limit
