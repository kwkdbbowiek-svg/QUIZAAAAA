import asyncio
from shared.database.base import AsyncSessionLocal
from shared.database.models import User
from sqlalchemy import select

async def f():
    async with AsyncSessionLocal() as s:
        # telegram_id bo'yicha topish
        u = (await s.execute(
            select(User).where(User.telegram_id == 8590726796)
        )).scalar_one_or_none()

        if u:
            u.is_admin = True
            u.username = "xasan_coder"
            await s.commit()
            print('OK:', u.first_name, '@' + u.username, 'admin=', u.is_admin)
        else:
            print('Avval bota /start yuboring')

asyncio.run(f())
