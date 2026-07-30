#!/bin/bash
# Load deployment configuration and detect environment (Jenkins vs local)

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEPLOY_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
PROJECT_DIR="$(cd "$DEPLOY_DIR/.." && pwd)"

# Load config.sh (required)
if [ ! -f "$SCRIPT_DIR/config.sh" ]; then
    echo "[ERROR] config.sh not found" >&2
    exit 1
fi
source "$SCRIPT_DIR/config.sh"

# Validate required config
if [ -z "$PROJECT_NAME" ] || [ -z "$IMAGE_NAME" ] || [ -z "$COMPOSE_FILE" ]; then
    echo "[ERROR] Missing required config: PROJECT_NAME, IMAGE_NAME, COMPOSE_FILE" >&2
    exit 1
fi

# Detect Jenkins environment
if [ -n "${JENKINS_HOME:-}" ] || [ -n "${WORKSPACE:-}" ]; then
    export IS_JENKINS=true
    export ENV_FILE="${ENV_FILE:-$JENKINS_ENV_FILE}"
    export SECRETS_FILE="${SECRETS_FILE:-$JENKINS_SECRETS_FILE}"
    export PROJECT_DIR="${WORKSPACE:-$PROJECT_DIR}"
    
    if [ -z "$JENKINS_ENV_FILE" ] || [ -z "$JENKINS_SECRETS_FILE" ]; then
        echo "[ERROR] Missing Jenkins config: JENKINS_ENV_FILE, JENKINS_SECRETS_FILE" >&2
        exit 1
    fi
else
    export IS_JENKINS=false
fi

# Make compose file path absolute
if [[ "$COMPOSE_FILE" != /* ]]; then
    export COMPOSE_FILE="$PROJECT_DIR/$COMPOSE_FILE"
fi

# Load .env file helper
load_env_if_present() {
    local env_file="$PROJECT_DIR/.env"
    
    if [[ -f "$env_file" ]]; then
        set -a
        source "$env_file"
        set +a
        return 0
    else
        if [ "$IS_JENKINS" = "true" ]; then
            echo "[ERROR] .env file not found: $env_file" >&2
            return 1
        fi
        return 0
    fi
}

# Only execute when called directly (not when sourced)
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    load_env_if_present
fi
