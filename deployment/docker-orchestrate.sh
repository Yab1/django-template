#!/bin/bash

# Docker Orchestration Script
# This script manages Docker Compose operations
# Usage: ./deployment/docker-orchestrate.sh [command]
# Example: ./deployment/docker-orchestrate.sh up
# Example: ./deployment/docker-orchestrate.sh down

set -e  # Exit on any error

# Script configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

# Default configuration (customize via PROJECT_NAME env var)
PROJECT_NAME="${PROJECT_NAME:-ehr_django_template}"

# Parse command line arguments
COMMAND="${1:-up}"

# Compose file path (unified deployment)
COMPOSE_FILE="$PROJECT_DIR/deployment/docker-compose.yml"

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

log_warning() {
    echo "[WARNING] $1"
}

# Function to show usage information
usage() {
    echo "Usage: $0 [command]"
    echo
    echo "Commands:"
    echo "  up       Start services"
    echo "  down     Stop services"
    echo "  restart  Restart services"
    echo "  ps       Show service status"
    echo "  deploy   Deploy with optimized build and caching"
    echo
    echo "Examples:"
    echo "  $0 up       # Start services"
    echo "  $0 down     # Stop services"
    echo "  $0 restart  # Restart services"
    echo "  $0 ps       # Show status"
    echo "  $0 deploy   # Deploy with optimized build"
}

# Function to check if docker-compose file exists
check_compose_file() {
    if [[ ! -f "$COMPOSE_FILE" ]]; then
        log_error "Docker Compose file not found at: $COMPOSE_FILE"
        exit 1
    fi
}

# Function to check if Docker is running
check_docker() {
    if ! docker info >/dev/null 2>&1; then
        log_error "Docker is not running or not accessible."
        log_error "Please start Docker and try again."
        exit 1
    fi
}

# Function to load environment variables from .env file
load_env_if_present() {
    local env_file="$PROJECT_DIR/.env"
    
    if [[ -f "$env_file" ]]; then
        set -a
        source "$env_file"
        set +a
        log_success "Environment variables loaded from .env file"
    else
        log_warning "No .env file found at: $env_file"
    fi
}

# Function to initialize git submodules before Docker build
init_submodules() {
    cd "$PROJECT_DIR"
    
    log_info "Initializing git submodules..."
    
    # Use the submodule script (similar to install.sh approach)
    if [ -f "$PROJECT_DIR/scripts/submodule-init.sh" ]; then
        bash "$PROJECT_DIR/scripts/submodule-init.sh"
        return $?
    else
        log_warning "submodule-init.sh not found, falling back to manual initialization..."
        # Fallback to manual approach
        git submodule init 2>/dev/null || true
        git submodule update --init --recursive 2>/dev/null || return 1
        return 0
    fi
}

# Function to start services
start() {
    cd "$PROJECT_DIR"
    
    # Initialize git submodules BEFORE building Docker images
    # This ensures submodules are available in the Docker build context
    if ! init_submodules; then
        log_error "Submodule initialization failed. Cannot proceed with Docker build."
        log_error "Please run: make submodule-init && make submodule-update"
        exit 1
    fi
    
    log_info "Building images with BuildKit cache..."
    export DOCKER_BUILDKIT=1
    export COMPOSE_DOCKER_CLI_BUILD=1
    export DOCKER_BUILD_CONTEXT="$PROJECT_DIR"
    
    # Compose optional env flag
    compose_env_args=()
    if [[ -f .env ]]; then
        compose_env_args+=(--env-file .env)
    fi
    
    docker compose -p "$PROJECT_NAME" -f "$COMPOSE_FILE" "${compose_env_args[@]}" build --parallel --progress=plain
    
    log_info "Pulling external images..."
    docker compose -p "$PROJECT_NAME" -f "$COMPOSE_FILE" "${compose_env_args[@]}" pull --ignore-build-pending || log_warning "Some external images may not be available"
    
    log_info "Starting services..."
    docker compose -p "$PROJECT_NAME" -f "$COMPOSE_FILE" "${compose_env_args[@]}" up -d
    
    docker compose -p "$PROJECT_NAME" -f "$COMPOSE_FILE" "${compose_env_args[@]}" ps
}

# Function to stop services
stop() {
    cd "$PROJECT_DIR"
    
    # Compose optional env flag
    compose_env_args=()
    if [[ -f .env ]]; then
        compose_env_args+=(--env-file .env)
    fi
    
    docker compose -p "$PROJECT_NAME" -f "$COMPOSE_FILE" "${compose_env_args[@]}" down --remove-orphans
}

# Function to restart services
restart() {
    stop
    start
}

# Function to show service status
ps() {
    cd "$PROJECT_DIR"
    
    # Compose optional env flag
    compose_env_args=()
    if [[ -f .env ]]; then
        compose_env_args+=(--env-file .env)
    fi
    
    docker compose -p "$PROJECT_NAME" -f "$COMPOSE_FILE" "${compose_env_args[@]}" ps
}

# Function to deploy with optimized build and caching
deploy() {
    cd "$PROJECT_DIR"

    # Speed up builds and caching
    export DOCKER_BUILDKIT=1
    export COMPOSE_DOCKER_CLI_BUILD=1
    export DOCKER_BUILD_CONTEXT="$PROJECT_DIR"

    # Compose optional env flag
    compose_env_args=()
    if [[ -f .env ]]; then
        compose_env_args+=(--env-file .env)
    fi

    docker compose -p "$PROJECT_NAME" -f "$COMPOSE_FILE" "${compose_env_args[@]}" down --remove-orphans || true

    CURRENT_COMMIT=$(git rev-parse HEAD)
    IMAGE_NAME="${IMAGE_NAME:-ehr_django_template:latest}"

    if docker image inspect "$IMAGE_NAME" >/dev/null 2>&1; then
        if docker image inspect "$IMAGE_NAME" | grep -q "$CURRENT_COMMIT" 2>/dev/null; then
            log_success "Image is up-to-date with current commit. Skipping rebuild."
            REBUILD_NEEDED=false
        else
            log_info "Code has changed. Rebuilding image..."
            REBUILD_NEEDED=true
        fi
    else
        log_info "Image doesn't exist. Building for the first time..."
        REBUILD_NEEDED=true
    fi

    if [ "$REBUILD_NEEDED" = true ]; then
        # Initialize git submodules BEFORE building Docker images
        if ! init_submodules; then
            log_error "Submodule initialization failed. Cannot proceed with Docker build."
            log_error "Please run: make submodule-init && make submodule-update"
            exit 1
        fi
        
        log_info "Building Docker images..."
        docker compose -p "$PROJECT_NAME" -f "$COMPOSE_FILE" "${compose_env_args[@]}" build --progress=plain --parallel
        
        docker tag "$IMAGE_NAME" "${IMAGE_NAME%:latest}:${CURRENT_COMMIT}"
        log_success "Image built and tagged with commit: $CURRENT_COMMIT"
    else
        log_success "Using existing image. No rebuild needed."
    fi

    docker image prune -f || true

    docker compose -p "$PROJECT_NAME" -f "$COMPOSE_FILE" "${compose_env_args[@]}" up -d

    docker compose -p "$PROJECT_NAME" -f "$COMPOSE_FILE" "${compose_env_args[@]}" ps
}

# Main execution
main() {
    if [[ "$1" == "-h" || "$1" == "--help" ]]; then
        usage
        exit 0
    fi

    check_docker
    check_compose_file
    load_env_if_present

    case "$COMMAND" in
        "up")
            start
            ;;
        "down")
            stop
            ;;
        "restart")
            restart
            ;;
        "ps")
            ps
            ;;
        "deploy")
            deploy
            ;;
        *)
            log_error "Unknown command: $COMMAND"
            log_error "Available commands: up, down, restart, ps, deploy"
            usage
            exit 1
            ;;
    esac
}

# Run main function
main "$@"

