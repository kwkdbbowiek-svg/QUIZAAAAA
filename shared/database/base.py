"""
SQLAlchemy async database ulanishi
"""

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from shared.config import settings


engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncSession:
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
    """Jadvallarni yaratish — mavjud bo'lsa o'zgartirmaydi"""
    async with engine.begin() as conn:
        # checkfirst=True — jadval bo'lsa qayta yaratmaydi
        await conn.run_sync(Base.metadata.create_all, checkfirst=True)


async def alter_tables():
    """
    Yangi columnlarni qo'shish (migration o'rniga).
    Faqat mavjud bo'lmagan columnlarni qo'shadi.
    """
    alter_statements = [
        "ALTER TABLE questions ADD COLUMN IF NOT EXISTS time_limit INTEGER DEFAULT 30",
        "ALTER TABLE challenges ADD COLUMN IF NOT EXISTS question_ids JSONB DEFAULT '[]'",
        "ALTER TABLE challenges ADD COLUMN IF NOT EXISTS winners_paid BOOLEAN DEFAULT FALSE",
    ]
    async with engine.begin() as conn:
        for stmt in alter_statements:
            try:
                await conn.execute(__import__('sqlalchemy').text(stmt))
            except Exception as e:
                pass  # Column allaqachon mavjud bo'lsa xato chiqmaydi


async def drop_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
