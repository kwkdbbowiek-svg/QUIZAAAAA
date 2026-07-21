"""
Railway uchun asosiy ishga tushirish fayli.
API va Bot parallel ishlaydi.
"""

import asyncio
import multiprocessing
import subprocess
import sys
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def run_api():
    """FastAPI serverini ishga tushirish"""
    port = os.environ.get("PORT", "8000")
    subprocess.run([
        sys.executable, "-m", "uvicorn",
        "backend.main:app",
        "--host", "0.0.0.0",
        "--port", str(port),
        "--workers", "2",
    ])


def run_bot():
    """Telegram botni ishga tushirish"""
    subprocess.run([sys.executable, "-m", "bot.main"])


if __name__ == "__main__":
    # API va Bot ni alohida processda ishga tushirish
    api_process = multiprocessing.Process(target=run_api, name="API")
    bot_process = multiprocessing.Process(target=run_bot, name="Bot")

    api_process.start()
    logger.info("✅ API ishga tushdi")

    bot_process.start()
    logger.info("✅ Bot ishga tushdi")

    try:
        api_process.join()
        bot_process.join()
    except KeyboardInterrupt:
        logger.info("🛑 To'xtatilmoqda...")
        api_process.terminate()
        bot_process.terminate()
        sys.exit(0)
