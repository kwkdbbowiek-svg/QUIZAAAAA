# Railway.app Procfile
# API server va Bot parallel ishlasin

web: uvicorn backend.main:app --host 0.0.0.0 --port $PORT
bot: python -m bot.main
