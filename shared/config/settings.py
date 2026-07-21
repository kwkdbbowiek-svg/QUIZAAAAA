"""
Loyiha asosiy sozlamalari - Railway Environment Variables bilan ishlaydi
"""

from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import Optional
import secrets


class Settings(BaseSettings):
    # ─── Application ─────────────────────────────────────────────────────────
    APP_NAME: str = "EduQuiz Platform"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    SECRET_KEY: str = secrets.token_urlsafe(32)
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30 * 24 * 60  # 30 kun

    # ─── API ─────────────────────────────────────────────────────────────────
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000

    # ─── Database (Railway auto-provides DATABASE_URL) ────────────────────────
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/eduquiz"

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def fix_database_url(cls, v: str) -> str:
        """Railway ba'zan postgres:// beradi, asyncpg uchun to'g'irlaymiz"""
        if v and v.startswith("postgres://"):
            v = v.replace("postgres://", "postgresql+asyncpg://", 1)
        elif v and v.startswith("postgresql://") and "asyncpg" not in v:
            v = v.replace("postgresql://", "postgresql+asyncpg://", 1)
        return v

    # ─── Redis (Railway auto-provides REDIS_URL) ─────────────────────────────
    REDIS_URL: str = "redis://localhost:6379/0"

    # ─── Telegram Bot ─────────────────────────────────────────────────────────
    BOT_TOKEN: str = ""
    WEBAPP_URL: str = "https://localhost:3000"

    # ─── Admin ────────────────────────────────────────────────────────────────
    ADMIN_USERNAME: str = "admin"
    ADMIN_PASSWORD: str = "admin123"
    ADMIN_IDS: str = "[]"  # Railway'da string keladi: "123456,789012"

    @property
    def admin_ids_list(self) -> list[int]:
        """ADMIN_IDS stringini int listga aylantirish"""
        try:
            import json
            ids = json.loads(self.ADMIN_IDS)
            return [int(i) for i in ids]
        except Exception:
            # Vergul bilan ajratilgan format: "123,456"
            try:
                return [int(i.strip()) for i in self.ADMIN_IDS.split(",") if i.strip()]
            except Exception:
                return []

    # ─── Challenge Settings ───────────────────────────────────────────────────
    MIN_CHALLENGE_PLAYERS: int = 2
    MAX_CHALLENGE_PLAYERS: int = 1000
    DEFAULT_COMMISSION_PERCENT: float = 10.0

    # ─── Rating Settings ──────────────────────────────────────────────────────
    DAILY_RATING_KEY: str = "rating:daily"
    WEEKLY_RATING_KEY: str = "rating:weekly"
    GLOBAL_RATING_KEY: str = "rating:global"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "allow"


# Singleton instance
settings = Settings()
