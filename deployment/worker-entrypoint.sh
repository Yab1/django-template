#!/bin/sh
set -e

# Worker entrypoint — starts Celery / Temporal processes without web-server bootstrap.

if [ -n "${DB_WAIT_SECONDS:-}" ]; then
    echo "Waiting for database... (${DB_WAIT_SECONDS}s)"
    sleep "${DB_WAIT_SECONDS}"
fi

echo "Starting worker: $*"
exec "$@"
