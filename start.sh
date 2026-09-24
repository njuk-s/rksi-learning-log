#!/bin/sh
# Запуск приложения в контейнере: миграции, администратор, демо-данные, Gunicorn.
set -e

# Всё подготовительное - одной командой, чтобы Django загружался один раз.
python manage.py prestart

# --preload: приложение загружается один раз до запуска рабочих процессов.
# gthread: один процесс обслуживает несколько запросов потоками - этого
# достаточно для слабого процессора бесплатного хостинга.
# exec делает Gunicorn главным процессом контейнера.
exec gunicorn learning_log.wsgi:application     --bind "0.0.0.0:${PORT:-8000}"     --preload     --worker-class gthread     --workers "${WEB_CONCURRENCY:-2}"     --threads "${GUNICORN_THREADS:-4}"     --timeout 60     --access-logfile -
