#!/bin/bash
# Bring up shared infra (PostGIS, Redis, RabbitMQ, Mailpit, MinIO).
# Env: infra/.env (Jenkins copies JENKINS_ENV_FILE there).

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INFRA_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

while [[ $# -gt 0 ]]; do
	case "$1" in
		-h|--help)
			echo "Usage: $0"
			exit 0
			;;
		*)
			echo "unknown flag: $1" >&2
			exit 2
			;;
	esac
done

if [ ! -f "$INFRA_DIR/.env" ]; then
	echo "[ERROR] Missing $INFRA_DIR/.env — copy from .env.example or Jenkins env file" >&2
	exit 1
fi

cd "$INFRA_DIR"

echo "[INFO] Starting Django Template infra (postgres redis rabbitmq mailpit minio)..."
make up

echo "[INFO] Waiting for containers to become healthy..."
deadline=$((SECONDS + 120))
while true; do
	unhealthy="$(docker compose \
		-f compose.yml \
		-f compose.postgres.yml \
		-f compose.redis.yml \
		-f compose.rabbitmq.yml \
		-f compose.mailpit.yml \
		-f compose.minio.yml \
		-f compose.clamav.yml \
		--env-file .env \
		ps --format '{{.Name}} {{.Health}}' 2>/dev/null | awk '$2 == "unhealthy" {print}' || true)"

	starting="$(docker compose \
		-f compose.yml \
		-f compose.postgres.yml \
		-f compose.redis.yml \
		-f compose.rabbitmq.yml \
		-f compose.mailpit.yml \
		-f compose.minio.yml \
		-f compose.clamav.yml \
		--env-file .env \
		ps --format '{{.Name}} {{.Health}}' 2>/dev/null | awk '$2 == "starting" {print}' || true)"

	if [ -n "$unhealthy" ]; then
		echo "[ERROR] Unhealthy services:" >&2
		echo "$unhealthy" >&2
		make ps || true
		exit 1
	fi

	if [ -z "$starting" ]; then
		break
	fi

	if [ "$SECONDS" -ge "$deadline" ]; then
		echo "[ERROR] Timed out waiting for healthy infra" >&2
		make ps || true
		exit 1
	fi

	sleep 3
done

echo "[SUCCESS] Infra is up"
make ps
