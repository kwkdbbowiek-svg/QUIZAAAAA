"""
Autentifikatsiya middleware - har bir so'rovda foydalanuvchini DB ga saqlash/yangilash
"""

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery
from sqlalchemy import select
from datetime import datetime
from typing import Callable, Awaitable, Any

from shared.database.base import AsyncSessionLocal
from shared.database.models import User


class AuthMiddleware(BaseMiddleware):
    """
    Har bir xabar/callback'da foydalanuvchini avtomatik yaratish yoki yangilash.
    Foydalanuvchi ma'lumotlari handler'larga data["user"] orqali uzatiladi.
    """

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict], Awaitable[Any]],
        event: TelegramObject,
        data: dict
    ) -> Any:
        # Telegram foydalanuvchisini olish
        telegram_user = None
        if isinstance(event, Message) and event.from_user:
            telegram_user = event.from_user
        elif isinstance(event, CallbackQuery) and event.from_user:
            telegram_user = event.from_user

        if telegram_user:
            async with AsyncSessionLocal() as session:
                result = await session.execute(
                    select(User).where(User.telegram_id == telegram_user.id)
                )
                user = result.scalar_one_or_none()

                if not user:
                    user = User(
                        telegram_id=telegram_user.id,
                        username=telegram_user.username,
                        first_name=telegram_user.first_name or "User",
                        last_name=telegram_user.last_name,
                        language_code=telegram_user.language_code or "uz",
                    )
                    session.add(user)
                else:
                    # Ma'lumotlarni yangilash
                    user.username = telegram_user.username
                    user.first_name = telegram_user.first_name or user.first_name
                    user.last_name = telegram_user.last_name
                    user.last_active = datetime.utcnow()

                await session.commit()
                await session.refresh(user)
                # Session yopilgandan keyin ham user ob'ekti ishlashi uchun
                session.expunge(user)
                data["user"] = user

        return await handler(event, data)
