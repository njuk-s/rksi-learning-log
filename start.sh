#!/bin/sh
# Запуск приложения в контейнере: миграции, администратор, демо-данные, Gunicorn.
set -e

python manage.py migrate --noinput
python manage.py ensure_admin
if [ "${SEED_DEMO:-False}" = "True" ]; then
    python manage.py seed_demo
fi

# exec делает Gunicorn главным процессом контейнера.
exec gunicorn learning_log.wsgi:application \
    --bind "0.0.0.0:${PORT:-8000}" \
    --workers "${WEB_CONCURRENCY:-2}" \
    --timeout 60 \
    --access-logfile -
