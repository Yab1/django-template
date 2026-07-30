#!/bin/sh
set -e

# Entrypoint script
# Handles database migrations and starts the application server

# Wait for database to be ready
if [ -n "${DB_WAIT_SECONDS:-}" ]; then
    echo "Waiting for database... (${DB_WAIT_SECONDS}s)"
    sleep "${DB_WAIT_SECONDS}"
fi

# Apply database migrations (idempotent)
echo "Applying database migrations..."
python manage.py migrate --noinput

# Load superusers if needed (run before starting server)
if [ -n "${LOAD_SUPERUSERS:-}" ] && [ "${LOAD_SUPERUSERS}" != "0" ]; then
    echo "Loading superusers..."
    python manage.py load_superusers 2>/dev/null || echo "No superusers to load or command not available"
fi

# Collect static files if enabled (default: enabled)
if [ -z "${COLLECT_STATIC:-}" ] || [ "${COLLECT_STATIC}" != "0" ]; then
    echo "Collecting static files..."
    python manage.py collectstatic --noinput --clear
else
    echo "Skipping static files collection (COLLECT_STATIC=0)"
fi

# Start ASGI server (Gunicorn+Uvicorn)
# Using exec to replace shell process for proper signal handling
echo "Starting Gunicorn+Uvicorn (ASGI) on port ${PORT:-7002}..."
exec gunicorn --config deployment/gunicorn.config.py config.asgi:application