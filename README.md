# EduQuiz & Challenge Platform

## 🎯 Loyiha Haqida
Telegram bot orqali boshqariladigan, to'liq xavfsizlik himoyasiga ega, professional ta'lim va o'yin platformasi.

## 🛠 Texnologik Stek
- **Backend**: FastAPI + Python 3.11
- **Bot**: Aiogram 3.x
- **Database**: PostgreSQL (SQLAlchemy ORM)
- **Cache/Real-time**: Redis
- **Frontend**: React + TailwindCSS
- **Deployment**: Railway.app (Docker)

## 📁 Loyiha Strukturasi
```
eduquiz-platform/
├── backend/                 # FastAPI backend
│   ├── api/                # API endpoints
│   ├── core/               # Core settings
│   ├── models/             # Database models
│   ├── schemas/            # Pydantic schemas
│   ├── services/           # Business logic
│   └── utils/              # Utility functions
├── bot/                    # Telegram bot
│   ├── handlers/           # Message handlers
│   ├── keyboards/          # Keyboards
│   ├── middlewares/        # Middlewares
│   └── utils/              # Bot utilities
├── frontend/               # React frontend
│   ├── src/
│   │   ├── components/     # React components
│   │   ├── pages/          # Pages
│   │   └── services/       # API services
│   └── public/
├── shared/                 # Shared code
│   ├── database/           # DB models & connection
│   └── config/             # Configuration
├── alembic/                # Database migrations
├── docker-compose.yml      # Local development
├── Dockerfile              # Production Docker
├── railway.toml            # Railway config
├── Procfile                # Railway/Heroku process
└── requirements.txt        # Python dependencies
```

## 🚀 Railway.app Deploy
1. GitHub repository bilan bog'lang
2. Environment variables o'rnating
3. Automatic deploy ishlaydi

## 🔐 Xavfsizlik
- Bot xabarlari: `protect_content=True`
- Web App: Copy/Screenshot protection
- JWT Authentication
- Rate limiting
- SQL injection prevention

## 📊 Features
- ✅ Foydalanuvchi ro'yxatdan o'tishi
- ✅ Majburiy kanal obunasi
- ✅ Bepul test va quiz
- ✅ Pullik Challenge'lar
- ✅ Real-time reyting (Redis)
- ✅ Admin panel
- ✅ Broadcast tizimi
- ✅ Balans boshqaruvi
