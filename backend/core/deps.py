"""
FastAPI Dependencies - Auth, DB, Redis
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional

from shared.database import get_db, User
from shared.database.redis_client import get_redis, RatingService, CacheService
from .security import decode_token
import redis.asyncio as aioredis

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    """Joriy autentifikatsiyalangan foydalanuvchini olish"""
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Autentifikatsiya talab etiladi",
        )
    
    payload = decode_token(token)
    telegram_id = payload.get("sub")
    
    if not telegram_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token yaroqsiz")
    
    result = await db.execute(select(User).where(User.telegram_id == int(telegram_id)))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Foydalanuvchi topilmadi")
    
    if user.status.value == "banned":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Akkaunt bloklangan")
    
    return user


async def get_admin_user(current_user: User = Depends(get_current_user)) -> User:
    """Admin foydalanuvchini tekshirish"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin huquqlari talab etiladi"
        )
    return current_user


async def get_rating_service(redis: aioredis.Redis = Depends(get_redis)) -> RatingService:
    return RatingService(redis)


async def get_cache_service(redis: aioredis.Redis = Depends(get_redis)) -> CacheService:
    return CacheService(redis)
