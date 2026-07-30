#!/bin/bash
# Materialize .env / .secrets.yml into the workspace for docker compose.
#
# Resolution order (first wins):
#   1. ENV_FILE / SECRETS_FILE env vars (Jenkins Credentials secret-file bind paths)
#   2. Legacy host paths from config.sh (JENKINS_ENV_FILE / JENKINS_SECRETS_FILE)
#
# Set REQUIRE_SECRETS=0 to allow missing secrets (default: required).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=load-config.sh
source "$SCRIPT_DIR/load-config.sh"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[PREPARE]${NC} $1"; }
log_ok() { echo -e "${GREEN}[PREPARE]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[PREPARE]${NC} $1"; }
log_error() { echo -e "${RED}[PREPARE]${NC} $1" >&2; }

REQUIRE_SECRETS="${REQUIRE_SECRETS:-1}"
cd "$PROJECT_DIR"

resolve_env_src() {
    if [[ -n "${ENV_FILE:-}" && -f "$ENV_FILE" ]]; then
        echo "$ENV_FILE"
        return 0
    fi
    if [[ -n "${JENKINS_ENV_FILE:-}" && -f "$JENKINS_ENV_FILE" ]]; then
        echo "$JENKINS_ENV_FILE"
        return 0
    fi
    return 1
}

resolve_secrets_src() {
    if [[ -n "${SECRETS_FILE:-}" && -f "$SECRETS_FILE" ]]; then
        echo "$SECRETS_FILE"
        return 0
    fi
    if [[ -n "${JENKINS_SECRETS_FILE:-}" && -f "$JENKINS_SECRETS_FILE" ]]; then
        echo "$JENKINS_SECRETS_FILE"
        return 0
    fi
    return 1
}

log_info "Preparing environment files in ${PROJECT_DIR}"

if ! env_src="$(resolve_env_src)"; then
    log_error "Environment file not found."
    log_error "Provide Credentials secret-file via ENV_FILE, or host path JENKINS_ENV_FILE=${JENKINS_ENV_FILE:-unset}"
    exit 1
fi

umask 077
cp -- "$env_src" "$PROJECT_DIR/.env"
chmod 600 "$PROJECT_DIR/.env"
log_ok "Copied env -> .env (source=${env_src})"

if secrets_src="$(resolve_secrets_src)"; then
    cp -- "$secrets_src" "$PROJECT_DIR/.secrets.yml"
    chmod 600 "$PROJECT_DIR/.secrets.yml"
    log_ok "Copied secrets -> .secrets.yml (source=${secrets_src})"
else
    if [[ "$REQUIRE_SECRETS" == "1" ]]; then
        log_error "Secrets file not found and REQUIRE_SECRETS=1."
        log_error "Provide Credentials secret-file via SECRETS_FILE, or host path JENKINS_SECRETS_FILE=${JENKINS_SECRETS_FILE:-unset}"
        exit 1
    fi
    log_warn "Secrets file not found; continuing because REQUIRE_SECRETS=0"
    rm -f "$PROJECT_DIR/.secrets.yml"
fi
