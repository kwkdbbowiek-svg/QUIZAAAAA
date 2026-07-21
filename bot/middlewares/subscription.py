"""
Majburiy kanal obuna middleware
"""

from aiogram import BaseMiddleware, Bot
from aiogram.types import (
    TelegramObject, Message, CallbackQuery,
    InlineKeyboardMarkup, InlineKeyboardButton
)
from sqlalchemy import select
from typing import Callable, Awaitable, Any

from shared.database.base import AsyncSessionLocal
from shared.database.models import User, RequiredChannel


class SubscriptionMiddleware(BaseMiddleware):
    """
    Har bir so'rovda foydalanuvchining kanallarga obunasini tekshirish.
    Obuna bo'lmagan foydalanuvchiga obuna qilish uchun tugmalar ko'rsatiladi.
    """

    # Bu buyruqlar uchun obuna tekshirilmaydi
    EXCLUDED_COMMANDS = {"/start", "/help", "/admin"}

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict], Awaitable[Any]],
        event: TelegramObject,
        data: dict
    ) -> Any:
        user: User = data.get("user")

        # Foydalanuvchi yo'q yoki admin bo'lsa — o'tkazib yuborish
        if not user or user.is_admin:
            return await handler(event, data)

        # /start kabi komandalar uchun tekshirishdan o'tkazish
        if isinstance(event, Message):
            text = event.text or ""
            if any(text.startswith(cmd) for cmd in self.EXCLUDED_COMMANDS):
                return await handler(event, data)

        # Kanallarni DB dan olish
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(RequiredChannel).where(RequiredChannel.is_active == True)
            )
            channels = result.scalars().all()

        if not channels:
            return await handler(event, data)

        # Bot instance — Aiogram 3.x da data["bot"] orqali keladi
        bot: Bot = data.get("bot")
        if not bot:
            return await handler(event, data)

        unsubscribed = []
        for channel in channels:
            try:
                member = await bot.get_chat_member(channel.channel_id, user.telegram_id)
                if member.status in ("left", "kicked", "restricted"):
                    unsubscribed.append(channel)
            except Exception:
                # Kanal topilmasa yoki bot admin emas — o'tkazib yuborish
                pass

        if not unsubscribed:
            return await handler(event, data)

        # Obuna qilish tugmalarini yaratish
        keyboard = []
        for ch in unsubscribed:
            link = ch.channel_link or f"https://t.me/{ch.channel_id.lstrip('@')}"
            keyboard.append([
                InlineKeyboardButton(
                    text=f"📢 {ch.channel_name} ga obuna bo'ling",
                    url=link
                )
            ])
        keyboard.append([
            InlineKeyboardButton(
                text="✅ Obuna bo'ldim, tekshiring",
                callback_data="check_subscription"
            )
        ])

        markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
        message_text = (
            "⚠️ <b>Botdan foydalanish uchun quyidagi kanallarga obuna bo'lishingiz shart:</b>\n\n"
            + "\n".join(f"• {ch.channel_name}" for ch in unsubscribed)
            + "\n\n📌 Obuna bo'lgandan so'ng <b>\"✅ Obuna bo'ldim\"</b> tugmasini bosing."
        )

        if isinstance(event, Message):
            await event.answer(message_text, reply_markup=markup)
        elif isinstance(event, CallbackQuery):
            if event.data != "check_subscription":
                await event.message.answer(message_text, reply_markup=markup)
                await event.answer()

        return  # Handler'ni to'xtatish
