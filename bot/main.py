"""
EduQuiz Telegram Bot - Aiogram 3.x
"""

import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.redis import RedisStorage

from shared.config import settings
from shared.database.base import create_tables
from shared.database.redis_client import get_redis

from bot.handlers import start, quiz, challenge, profile, admin
from bot.middlewares.auth import AuthMiddleware
from bot.middlewares.subscription import SubscriptionMiddleware
from bot.utils.broadcast import BroadcastWorker

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def main():
    """Botni ishga tushirish"""
    logger.info("🤖 Bot ishga tushmoqda...")

    # Database tayyorlash
    await create_tables()

    # Redis storage (FSM uchun)
    redis = await get_redis()
    storage = RedisStorage(redis=redis)

    # Bot instance
    bot = Bot(
        token=settings.BOT_TOKEN,
        default=DefaultBotProperties(
            parse_mode=ParseMode.HTML,
            protect_content=True,  # 🔒 Barcha xabarlar himoyalangan
        )
    )

    # Dispatcher
    dp = Dispatcher(storage=storage)

    # Middleware'larni ro'yxatdan o'tkazish
    dp.message.middleware(AuthMiddleware())
    dp.callback_query.middleware(AuthMiddleware())

    # Obuna middleware (admin xabarlaridan tashqari)
    dp.message.middleware(SubscriptionMiddleware())
    dp.callback_query.middleware(SubscriptionMiddleware())

    # Handlerlarni ro'yxatdan o'tkazish
    dp.include_router(start.router)
    dp.include_router(quiz.router)
    dp.include_router(challenge.router)
    dp.include_router(profile.router)
    dp.include_router(admin.router)

    # Broadcast worker
    broadcast_worker = BroadcastWorker(bot, redis)

    logger.info("✅ Bot muvaffaqiyatli ishga tushdi!")

    try:
        await asyncio.gather(
            dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types()),
            broadcast_worker.run(),
        )
    finally:
        await bot.session.close()
        logger.info("👋 Bot to'xtatildi")


if __name__ == "__main__":
    asyncio.run(main())
