"""
Majburiy kanal obuna middleware — har so'rovda tekshiradi
"""

from aiogram import BaseMiddleware, Bot
from aiogram.types import TelegramObject, Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy import select
from typing import Callable, Awaitable, Any

from shared.database.base import AsyncSessionLocal
from shared.database.models import User, RequiredChannel

EXCLUDED_COMMANDS = {"/start", "/help"}
EXCLUDED_CALLBACKS = {"check_subscription"}


class SubscriptionMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict], Awaitable[Any]],
        event: TelegramObject,
        data: dict
    ) -> Any:
        user: User = data.get("user")

        # Admin yoki ro'yxatsiz — o'tkazib yuborish
        if not user or user.is_admin:
            return await handler(event, data)

        # Excluded komandalar
        if isinstance(event, Message):
            text = event.text or ""
            if any(text.startswith(cmd) for cmd in EXCLUDED_COMMANDS):
                return await handler(event, data)

        if isinstance(event, CallbackQuery):
            if event.data in EXCLUDED_CALLBACKS:
                return await handler(event, data)

        # Faol kanallarni olish
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(RequiredChannel).where(RequiredChannel.is_active == True)
            )
            channels = result.scalars().all()

        if not channels:
            return await handler(event, data)

        bot: Bot = data.get("bot")
        if not bot:
            return await handler(event, data)

        # Obunani tekshirish
        unsubscribed = []
        for ch in channels:
            try:
                member = await bot.get_chat_member(ch.channel_id, user.telegram_id)
                if member.status in ("left", "kicked"):
                    unsubscribed.append(ch)
            except Exception:
                pass

        if not unsubscribed:
            return await handler(event, data)

        # Obuna qilish tugmalari
        keyboard = []
        for ch in unsubscribed:
            link = ch.channel_link or f"https://t.me/{ch.channel_id.lstrip('@')}"
            keyboard.append([InlineKeyboardButton(text=f"📢 {ch.channel_name}", url=link)])
        keyboard.append([InlineKeyboardButton(text="✅ Obuna bo'ldim", callback_data="check_subscription")])

        markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
        text = (
            "⚠️ <b>Quyidagi kanallarga obuna bo'ling:</b>\n\n"
            + "\n".join(f"• {ch.channel_name}" for ch in unsubscribed)
            + "\n\n✅ Obuna bo'lgandan so'ng tugmani bosing."
        )

        if isinstance(event, Message):
            await event.answer(text, reply_markup=markup)
        elif isinstance(event, CallbackQuery):
            await event.message.answer(text, reply_markup=markup)
            await event.answer()

        return  # Handler'ni to'xtatish
