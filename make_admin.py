import asyncio
from shared.database.base import AsyncSessionLocal
from shared.database.models import User
from sqlalchemy import select


async def make_admin():
    async with AsyncSessionLocal() as s:
        r = await s.execute(select(User).where(User.telegram_id == 8590726796))
        u = r.scalar_one_or_none()
        if u:
            u.is_admin = True
            await s.commit()
            print('Admin qilindi:', u.full_name)
        else:
            print('Avval bota /start yuboring')


asyncio.run(make_admin())
