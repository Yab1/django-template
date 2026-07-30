#!/bin/bash
set -e

# Deployment configuration
PROJECT_DIR="/var/lib/jenkins/workspace/ehr-django-template"
ENV_FILE="/var/lib/jenkins/api/ehr/ehr_django_template.env"
SECRETS_FILE="/var/lib/jenkins/api/secrets.yml"

# Logging functions
log_info() {
    echo "[INFO] $1"
}

log_error() {
    echo "[ERROR] $1" >&2
}

log_success() {
    echo "[SUCCESS] $1"
}

log_info "----------------------------"
log_info "EHR DJANGO TEMPLATE DEPLOYMENT"
log_info "----------------------------"

cd "$PROJECT_DIR" || {
    log_error "Failed to change directory to $PROJECT_DIR"
    exit 1
}

log_info "Copying environment file..."
if ! cp "$ENV_FILE" .env; then
    log_error "Failed to copy environment file from $ENV_FILE"
    exit 1
fi

log_info "Copying secrets file..."
if ! cp "$SECRETS_FILE" .secrets.yml; then
    log_error "Failed to copy secrets file from $SECRETS_FILE"
    exit 1
fi

# Export env so compose resolves ${...}
log_info "Loading environment variables..."
set -a
source .env
set +a

log_info "Deploying infrastructure (via orchestrator)..."
if ! ./deployment/docker-orchestrate.sh deploy; then
    log_error "Infrastructure deployment failed"
    exit 1
fi

log_info "Waiting for Django service to be ready..."
sleep 20

log_success "EHR Django Template is ready"

log_info "------------------------"
log_success "DEPLOYMENT COMPLETE"
log_info "------------------------"