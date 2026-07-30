#!/bin/bash
# Preflight checks before deploy. Fail fast on missing tooling / files.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=load-config.sh
source "$SCRIPT_DIR/load-config.sh"

RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[PREFLIGHT]${NC} $1"; }
log_ok() { echo -e "${GREEN}[PREFLIGHT]${NC} $1"; }
log_error() { echo -e "${RED}[PREFLIGHT]${NC} $1" >&2; }

fail=0

require_cmd() {
    if ! command -v "$1" >/dev/null 2>&1; then
        log_error "Missing required command: $1"
        fail=1
    else
        log_ok "Found $1"
    fi
}

log_info "Workspace: ${PROJECT_DIR}"
log_info "Compose:   ${COMPOSE_FILE}"

require_cmd docker
require_cmd curl
require_cmd git

if ! docker info >/dev/null 2>&1; then
    log_error "Docker daemon not reachable (is agent labeled / docker group OK?)"
    fail=1
else
    log_ok "Docker daemon OK"
fi

if ! docker compose version >/dev/null 2>&1; then
    log_error "docker compose plugin missing"
    fail=1
else
    log_ok "docker compose OK"
fi

for f in \
    "$COMPOSE_FILE" \
    "$SCRIPT_DIR/deploy.sh" \
    "$SCRIPT_DIR/prepare-env.sh" \
    "$SCRIPT_DIR/config.sh" \
    "$DEPLOY_DIR/nginx/app-active.conf.template"
do
    if [[ ! -e "$f" ]]; then
        log_error "Missing required file: $f"
        fail=1
    fi
done

if [[ ! -x "$SCRIPT_DIR/deploy.sh" ]]; then
    log_error "deploy.sh is not executable"
    fail=1
fi

if [[ ! -x "$SCRIPT_DIR/prepare-env.sh" ]]; then
    log_error "prepare-env.sh is not executable"
    fail=1
fi

cd "$PROJECT_DIR"
if ! git rev-parse HEAD >/dev/null 2>&1; then
    log_error "Not a git checkout / cannot resolve HEAD"
    fail=1
else
    log_ok "Git HEAD=$(git rev-parse --short HEAD)"
fi

disk_avail_kb=$(df -Pk "$PROJECT_DIR" | awk 'NR==2 {print $4}')
if [[ -n "${disk_avail_kb:-}" && "$disk_avail_kb" -lt 1048576 ]]; then
    log_error "Low disk (<1GiB free on workspace volume): ${disk_avail_kb} KiB"
    fail=1
else
    log_ok "Disk space OK (${disk_avail_kb:-unknown} KiB free)"
fi

if [[ "$fail" -ne 0 ]]; then
    log_error "Preflight failed"
    exit 1
fi

log_ok "Preflight passed"
