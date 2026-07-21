# 🚀 Railway.app Deploy Qo'llanmasi

## 1. GitHub'ga yuklash
```bash
git init
git add .
git commit -m "Initial commit: EduQuiz Platform"
git remote add origin https://github.com/yourusername/eduquiz-platform.git
git push -u origin main
```

## 2. Railway.app da loyiha yaratish
1. https://railway.app ga kiring
2. **New Project** → **Deploy from GitHub**
3. Repository'ni tanlang

## 3. PostgreSQL qo'shish
1. **New** → **Database** → **Add PostgreSQL**
2. `DATABASE_URL` avtomatik belgilanadi

## 4. Redis qo'shish
1. **New** → **Database** → **Add Redis**
2. `REDIS_URL` avtomatik belgilanadi

## 5. Environment Variables (Railway Dashboard → Variables)
```
BOT_TOKEN=your_telegram_bot_token
SECRET_KEY=super-secret-random-key-32-chars
WEBAPP_URL=https://your-app.railway.app
ADMIN_IDS=["123456789"]
DEBUG=false
```

## 6. Bot uchun alohida service (ixtiyoriy)
Railway'da ikki service yaratib, birini API, birini Bot sifatida ishlatish:

**API Service:**
```
Start Command: uvicorn backend.main:app --host 0.0.0.0 --port $PORT
```

**Bot Service:**
```
Start Command: python -m bot.main
```

## 7. Frontend Deploy (Vercel/Railway)
```bash
cd frontend
npm install
npm run build
```
Yoki Vercel'ga:
```bash
vercel --prod
```

## 8. Database Migration
```bash
alembic upgrade head
```

## 9. Admin foydalanuvchi qo'shish
```python
# Python shell yoki script orqali
import asyncio
from shared.database.base import AsyncSessionLocal
from shared.database.models import User

async def make_admin(telegram_id: int):
    async with AsyncSessionLocal() as session:
        from sqlalchemy import select
        result = await session.execute(select(User).where(User.telegram_id == telegram_id))
        user = result.scalar_one_or_none()
        if user:
            user.is_admin = True
            await session.commit()
            print(f"✅ {user.full_name} admin qilindi")

asyncio.run(make_admin(YOUR_TELEGRAM_ID))
```

## 🔐 Xavfsizlik Eslatmalar
- `SECRET_KEY` ni har bir muhitda alohida va kuchli qiling
- `BOT_TOKEN` ni hech qachon commit qilmang
- Production'da `DEBUG=false` bo'lishi shart
- ADMIN_IDS ro'yxatini ehtiyotkorlik bilan belgilang
