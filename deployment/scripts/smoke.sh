#!/bin/bash
# Post-deploy smoke: hit proxy health endpoint on the deploy host.
set -euo pipefail

HEALTH_URL="${HEALTH_URL:-http://127.0.0.1:6000/health/}"
SMOKE_RETRIES="${SMOKE_RETRIES:-15}"
SMOKE_SLEEP_SECONDS="${SMOKE_SLEEP_SECONDS:-2}"

echo "[SMOKE] Checking ${HEALTH_URL} (retries=${SMOKE_RETRIES})"

i=0
while [[ "$i" -lt "$SMOKE_RETRIES" ]]; do
    if curl -sfS "$HEALTH_URL" >/dev/null; then
        echo "[SMOKE] OK"
        exit 0
    fi
    i=$((i + 1))
    sleep "$SMOKE_SLEEP_SECONDS"
done

echo "[SMOKE] FAILED after ${SMOKE_RETRIES} attempts: ${HEALTH_URL}" >&2
exit 1
