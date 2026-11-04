#!/bin/sh
set -e

# API entrypoint. Migrations run in the one-shot migrate container (deploy.sh).
# This process only collectstatic (optional) then gunicorn.

if [ -n "${DB_WAIT_SECONDS:-}" ]; then
    echo "Waiting for database... (${DB_WAIT_SECONDS}s)"
    sleep "${DB_WAIT_SECONDS}"
fi

if [ -z "${COLLECT_STATIC:-}" ] || [ "${COLLECT_STATIC}" != "0" ]; then
    echo "Collecting static files..."
    python manage.py collectstatic --noinput --clear
else
    echo "Skipping static files collection (COLLECT_STATIC=0)"
fi

echo "django-template-entrypoint: ready-for-gunicorn"
echo "Starting Gunicorn+Uvicorn (ASGI) on port ${PORT:-8000}..."
exec gunicorn --config deploy/gunicorn.config.py config.asgi:application
