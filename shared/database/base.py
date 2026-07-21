"""
SQLAlchemy async database ulanishi va base model
"""

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from shared.config import settings


# Async engine
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)

# Session factory
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


class Base(DeclarativeBase):
    """Barcha modellar uchun asosiy klass - faqat DeclarativeBase"""
    pass


async def get_db() -> AsyncSession:
    """FastAPI dependency - DB session olish"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def create_tables():
    """Barcha jadvallarni yaratish"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def drop_tables():
    """Barcha jadvallarni o'chirish (faqat dev uchun)"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
