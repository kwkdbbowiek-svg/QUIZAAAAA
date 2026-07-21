# Multi-stage Docker build for Railway.app

# ========== Python Backend & Bot ==========
FROM python:3.11-slim AS python-base

WORKDIR /app

# System dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY backend/ ./backend/
COPY bot/ ./bot/
COPY shared/ ./shared/
COPY alembic.ini .
COPY alembic/ ./alembic/

# ========== Frontend Build ==========
FROM node:18-alpine AS frontend-build

WORKDIR /app/frontend

# Install dependencies
COPY frontend/package*.json ./
RUN npm ci

# Copy source and build
COPY frontend/ ./
RUN npm run build

# ========== Final Stage ==========
FROM python:3.11-slim AS final

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    nginx \
    supervisor \
    && rm -rf /var/lib/apt/lists/*

# Copy Python dependencies
COPY --from=python-base /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=python-base /usr/local/bin /usr/local/bin

# Copy application
COPY --from=python-base /app /app

# Copy frontend build
COPY --from=frontend-build /app/frontend/dist /app/frontend/dist

# Nginx configuration for serving frontend
RUN echo 'server {\n\
    listen 3000;\n\
    root /app/frontend/dist;\n\
    index index.html;\n\
    location / {\n\
        try_files $uri $uri/ /index.html;\n\
    }\n\
}' > /etc/nginx/sites-available/default

# Expose ports
EXPOSE 8000 3000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

# Default command
CMD ["python", "run.py"]
