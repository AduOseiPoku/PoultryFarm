#!/bin/sh
set -e

echo "==> Running database migrations..."
python manage.py migrate --noinput

echo "==> Ensuring static files are collected..."
python manage.py collectstatic --noinput --clear

echo "==> Starting Gunicorn on port ${PORT:-8000}..."
exec gunicorn config.wsgi:application \
    --bind 0.0.0.0:${PORT:-8000} \
    --workers ${GUNICORN_WORKERS:-3} \
    --threads ${GUNICORN_THREADS:-2} \
    --timeout ${GUNICORN_TIMEOUT:-120} \
    --access-logfile - \
    --error-logfile -
