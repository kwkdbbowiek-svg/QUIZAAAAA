"""
Majburiy kanal obuna middleware — har so'rovda tekshiradi
"""

from aiogram import BaseMiddleware, Bot
from aiogram.types import TelegramObject, Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy import select
from typing import Callable, Awaitable, Any
import logging

from shared.database.base import AsyncSessionLocal
from shared.database.models import User, RequiredChannel
from bot.utils.channel_helper import format_channel_link, check_user_subscription

logger = logging.getLogger(__name__)

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

        # Admin, ro'yxatsiz yoki user yo'q — o'tkazib yuborish
        if not user or user.is_admin or not user.is_registered:
            return await handler(event, data)

        # /start va /help komandalarini doim o'tkazish
        if isinstance(event, Message):
            text = event.text or ""
            if any(text.startswith(cmd) for cmd in EXCLUDED_COMMANDS):
                return await handler(event, data)

        # check_subscription callback'ini doim o'tkazish
        if isinstance(event, CallbackQuery):
            if event.data in EXCLUDED_CALLBACKS:
                return await handler(event, data)

        # Faol kanallarni olish
        try:
            async with AsyncSessionLocal() as session:
                result = await session.execute(
                    select(RequiredChannel).where(RequiredChannel.is_active == True)
                )
                channels = result.scalars().all()
        except Exception as e:
            logger.error(f"Kanallarni olishda xato: {e}")
            # Xato bo'lsa ham davom ettirish
            return await handler(event, data)

        # Agar majburiy kanallar yo'q bo'lsa
        if not channels:
            return await handler(event, data)

        bot: Bot = data.get("bot")
        if not bot:
            return await handler(event, data)

        # Obunani tekshirish
        unsubscribed = []
        for ch in channels:
            is_subscribed = await check_user_subscription(bot, ch.channel_id, user.telegram_id)
            if not is_subscribed:
                unsubscribed.append(ch)

        # Agar barcha kanallarga obuna bo'lgan bo'lsa
        if not unsubscribed:
            return await handler(event, data)

        # Obuna qilish tugmalari
        keyboard = []
        for ch in unsubscribed:
            link = format_channel_link(ch.channel_id, ch.channel_link)
            keyboard.append([InlineKeyboardButton(text=f"📢 {ch.channel_name}", url=link)])
        
        keyboard.append([InlineKeyboardButton(text="✅ Obuna bo'ldim", callback_data="check_subscription")])

        markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
        text = (
            "⚠️ <b>Botdan foydalanish uchun quyidagi kanallarga obuna bo'ling:</b>\n\n"
            + "\n".join(f"• {ch.channel_name}" for ch in unsubscribed)
            + "\n\n✅ Obuna bo'lgandan so'ng pastdagi tugmani bosing."
        )

        try:
            if isinstance(event, Message):
                await event.answer(text, reply_markup=markup)
            elif isinstance(event, CallbackQuery):
                await event.message.answer(text, reply_markup=markup)
                await event.answer("⚠️ Avval kanallarga obuna bo'ling!", show_alert=True)
        except Exception as e:
            logger.error(f"Obuna xabarini yuborishda xato: {e}")

        return  # Handler'ni to'xtatish
