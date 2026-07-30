#!/bin/bash
# Wipe workspace secret material. Safe to run when files absent.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEPLOY_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
PROJECT_DIR="$(cd "$DEPLOY_DIR/.." && pwd)"

cd "$PROJECT_DIR"
rm -f .env .secrets.yml
echo "[CLEANUP] Removed .env / .secrets.yml (if present)"
