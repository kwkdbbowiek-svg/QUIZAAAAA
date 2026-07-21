"""
Railway uchun asosiy ishga tushirish fayli.
API va Bot parallel ishlaydi.
"""

import asyncio
import os
import sys
import logging
import multiprocessing

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def run_api():
    """FastAPI serverini ishga tushirish"""
    import uvicorn
    # Railway $PORT env variable beradi
    port = int(os.environ.get("PORT", 8000))
    logger.info(f"🚀 API server port {port} da ishga tushmoqda...")
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=port,
        workers=1,
        log_level="info",
    )


def run_bot():
    """Telegram botni ishga tushirish"""
    import asyncio
    from bot.main import main
    logger.info("🤖 Bot ishga tushmoqda...")
    asyncio.run(main())


if __name__ == "__main__":
    mode = os.environ.get("RUN_MODE", "both")

    if mode == "api":
        # Faqat API
        run_api()
    elif mode == "bot":
        # Faqat Bot
        run_bot()
    else:
        # Ikkalasi parallel
        api_process = multiprocessing.Process(target=run_api, name="API", daemon=False)
        bot_process = multiprocessing.Process(target=run_bot, name="Bot", daemon=False)

        api_process.start()
        logger.info("✅ API process ishga tushdi")

        bot_process.start()
        logger.info("✅ Bot process ishga tushdi")

        try:
            api_process.join()
            bot_process.join()
        except KeyboardInterrupt:
            logger.info("🛑 To'xtatilmoqda...")
            api_process.terminate()
            bot_process.terminate()
            api_process.join()
            bot_process.join()
            sys.exit(0)
