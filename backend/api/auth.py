"""
Autentifikatsiya API - Telegram Web App uchun
"""

from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import hmac
import hashlib
import json
from urllib.parse import unquote

from shared.database import get_db, User
from shared.config import settings
from backend.core.security import create_telegram_token
from backend.schemas.user import TokenResponse, UserProfile
from shared.database.redis_client import get_redis, RatingService
import redis.asyncio as aioredis

router = APIRouter(prefix="/api/auth", tags=["Auth"])


def verify_telegram_webapp(init_data: str) -> dict:
    """
    Telegram Web App initData'ni tekshirish
    https://core.telegram.org/bots/webapps#validating-data-received-via-the-mini-app
    """
    try:
        parsed = {}
        for item in init_data.split("&"):
            key, value = item.split("=", 1)
            parsed[key] = unquote(value)
        
        data_check_string = "\n".join(
            f"{k}={v}" for k, v in sorted(parsed.items()) if k != "hash"
        )
        received_hash = parsed.get("hash", "")
        
        secret_key = hmac.new(
            key="WebAppData".encode(),
            msg=settings.BOT_TOKEN.encode(),
            digestmod=hashlib.sha256
        ).digest()

        calculated_hash = hmac.new(
            key=secret_key,
            msg=data_check_string.encode(),
            digestmod=hashlib.sha256
        ).hexdigest()
        
        if not hmac.compare_digest(calculated_hash, received_hash):
            raise ValueError("Hash mos kelmadi")
        
        user_data = json.loads(parsed.get("user", "{}"))
        return user_data
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Telegram ma'lumotlari yaroqsiz: {str(e)}"
        )


@router.post("/telegram", response_model=TokenResponse)
async def telegram_auth(
    init_data: str = Body(..., embed=True),
    db: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis)
):
    """Telegram Web App orqali autentifikatsiya"""
    user_data = verify_telegram_webapp(init_data)
    telegram_id = user_data.get("id")
    
    if not telegram_id:
        raise HTTPException(status_code=400, detail="Telegram ID topilmadi")
    
    # Foydalanuvchini topish yoki yaratish
    result = await db.execute(select(User).where(User.telegram_id == telegram_id))
    user = result.scalar_one_or_none()
    
    if not user:
        user = User(
            telegram_id=telegram_id,
            username=user_data.get("username"),
            first_name=user_data.get("first_name", "User"),
            last_name=user_data.get("last_name"),
            language_code=user_data.get("language_code", "uz"),
        )
        db.add(user)
        await db.flush()
    else:
        # Ma'lumotlarni yangilash
        user.username = user_data.get("username", user.username)
        user.first_name = user_data.get("first_name", user.first_name)
        user.last_name = user_data.get("last_name", user.last_name)
    
    await db.commit()
    await db.refresh(user)
    
    # Reyting ma'lumotlarini olish
    rating_service = RatingService(redis)
    ranks = await rating_service.get_user_ranks(user.telegram_id)
    
    token = create_telegram_token(user.telegram_id)
    
    user_profile = UserProfile.model_validate(user)
    user_profile.daily_rank = ranks["daily_rank"]
    user_profile.weekly_rank = ranks["weekly_rank"]
    user_profile.global_rank = ranks["global_rank"]
    
    return TokenResponse(access_token=token, user=user_profile)
