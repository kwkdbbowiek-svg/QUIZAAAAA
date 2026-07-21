"""
Background broadcast worker - Redis'dan broadcast tasklarni o'qib yuboradi
"""

import asyncio
import logging
from sqlalchemy import select, func
import redis.asyncio as aioredis

from shared.database.base import AsyncSessionLocal
from shared.database.models import User, BroadcastMessage

logger = logging.getLogger(__name__)


class BroadcastWorker:
    """
    Ma'lumotlar bazasidagi pending broadcast'larni background'da
    avtomatik yuborib turuvchi worker.
    """

    def __init__(self, bot, redis: aioredis.Redis, interval: int = 10):
        self.bot = bot
        self.redis = redis
        self.interval = interval  # Tekshirish intervali (soniya)
        self._running = False

    async def run(self):
        """Worker'ni ishga tushirish"""
        self._running = True
        logger.info("📣 Broadcast worker ishga tushdi")

        while self._running:
            try:
                await self.process_pending_broadcasts()
            except Exception as e:
                logger.error(f"Broadcast worker xatosi: {e}")
            await asyncio.sleep(self.interval)

    async def process_pending_broadcasts(self):
        """Pending broadcast'larni qayta ishlash"""
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(BroadcastMessage).where(
                    BroadcastMessage.status == "pending"
                ).limit(1)
            )
            broadcast = result.scalar_one_or_none()

            if not broadcast:
                return

            # Statusni yangilash
            from datetime import datetime
            broadcast.status = "sending"
            broadcast.started_at = datetime.utcnow()
            await session.commit()
            broadcast_id = broadcast.id
            broadcast_data = {
                "message_type": broadcast.message_type,
                "text": broadcast.text,
                "media_file_id": broadcast.media_file_id,
                "button_text": broadcast.button_text,
                "button_url": broadcast.button_url,
            }

        # Foydalanuvchilarga yuborish
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(User).where(User.status == "active")
            )
            users = result.scalars().all()

        success = 0
        failed = 0

        for user in users:
            try:
                await self._send_to_user(user.telegram_id, broadcast_data)
                success += 1
            except Exception:
                failed += 1
            await asyncio.sleep(0.05)  # Rate limiting

        # Natijani saqlash
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(BroadcastMessage).where(BroadcastMessage.id == broadcast_id)
            )
            bc = result.scalar_one_or_none()
            if bc:
                from datetime import datetime
                bc.status = "completed"
                bc.success_count = success
                bc.failed_count = failed
                bc.completed_at = datetime.utcnow()
                await session.commit()

        logger.info(f"Broadcast {broadcast_id} yakunlandi: {success} muvaffaqiyatli, {failed} muvaffaqiyatsiz")

    async def _send_to_user(self, telegram_id: int, data: dict):
        """Bir foydalanuvchiga xabar yuborish"""
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

        reply_markup = None
        if data.get("button_text") and data.get("button_url"):
            reply_markup = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text=data["button_text"], url=data["button_url"])]
            ])

        msg_type = data.get("message_type", "text")

        if msg_type == "text" and data.get("text"):
            await self.bot.send_message(
                telegram_id,
                data["text"],
                reply_markup=reply_markup,
            )
        elif msg_type == "photo" and data.get("media_file_id"):
            await self.bot.send_photo(
                telegram_id,
                data["media_file_id"],
                caption=data.get("text"),
                reply_markup=reply_markup,
            )
        elif msg_type == "video" and data.get("media_file_id"):
            await self.bot.send_video(
                telegram_id,
                data["media_file_id"],
                caption=data.get("text"),
                reply_markup=reply_markup,
            )

    def stop(self):
        self._running = False
