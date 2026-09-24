# Официальный облегчённый образ Python.
FROM python:3.12-slim

# Не создавать файлы .pyc и сразу выводить журналы приложения в Docker.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Сначала только зависимости - Docker закэширует их установку.
COPY requirements.txt .
RUN python -m pip install --no-cache-dir -r requirements.txt

COPY . .

# Статические файлы собираются один раз при сборке образа.
# Ключ здесь временный и нужен только для запуска collectstatic.
RUN DJANGO_SECRET_KEY=build-only-not-a-secret DJANGO_DEBUG=False \
    python manage.py collectstatic --noinput

# Приложение работает не от root. Каталог data - для SQLite-базы на томе.
RUN useradd --create-home --uid 1000 app \
    && mkdir -p /app/data \
    && chown -R app:app /app/data
USER app

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD python -c "import os, urllib.request; urllib.request.urlopen('http://127.0.0.1:%s/healthz/' % os.getenv('PORT', '8000'), timeout=3)"

CMD ["sh", "start.sh"]
