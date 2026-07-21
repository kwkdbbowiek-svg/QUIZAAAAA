import asyncio
from shared.database.base import AsyncSessionLocal
from shared.database.models import User
from sqlalchemy import select
async def f():
    async with AsyncSessionLocal() as s:
        u=(await s.execute(select(User).where(User.telegram_id==8590726796))).scalar_one_or_none()
        if u:u.is_admin=True;await s.commit();print('Admin OK:',u.first_name)
        else:print('Avval /start yuboring')
asyncio.run(f())
