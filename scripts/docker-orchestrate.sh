#!/bin/bash

# EHR Patient Service - Docker Orchestration Script
# This script manages Docker Compose operations for the EHR Patient Service
# Usage: ./scripts/docker-orchestrate.sh [environment] [command]
# Example: ./scripts/docker-orchestrate.sh production
# Example: ./scripts/docker-orchestrate.sh production down

set -e  # Exit on any error

# Script configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

# Default configuration
DEFAULT_ENVIRONMENT="production"
DEFAULT_PROJECT_NAME="ehr_patient"

# Parse command line arguments
ENVIRONMENT="${1:-$DEFAULT_ENVIRONMENT}"
COMMAND="${2:-up}"

# Set project name based on environment
PROJECT_NAME="${DEFAULT_PROJECT_NAME}_${ENVIRONMENT}"

# Compose file path based on environment
COMPOSE_FILE="$PROJECT_DIR/docker/$ENVIRONMENT/docker-compose.yml"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to show usage information
usage() {
    echo "Usage: $0 [environment] [command]"
    echo
    echo "Arguments:"
    echo "  environment    Environment to deploy (local, production, etc.)"
    echo "  command        Command to run (up, down, restart, ps, deploy)"
    echo
    echo "Examples:"
    echo "  $0 production                    # Start production environment"
    echo "  $0 production down               # Stop production environment"
    echo "  $0 production restart           # Restart production environment"
    echo "  $0 production ps                # Show status"
    echo "  $0 production deploy             # Deploy with Jenkins-style env handling"
    echo
    echo "Available environments:"
    for env_dir in "$PROJECT_DIR/docker"/*/; do
        if [[ -d "$env_dir" && -f "$env_dir/docker-compose.yml" ]]; then
            local env_name=$(basename "$env_dir")
            echo "  - $env_name"
        fi
    done
}

# Function to check if docker-compose file exists
check_compose_file() {
    if [[ ! -f "$COMPOSE_FILE" ]]; then
        print_error "Docker Compose file not found at: $COMPOSE_FILE"
        print_error "Available environments:"
        for env_dir in "$PROJECT_DIR/docker"/*/; do
            if [[ -d "$env_dir" && -f "$env_dir/docker-compose.yml" ]]; then
                local env_name=$(basename "$env_dir")
                echo "  - $env_name"
            fi
        done
        print_error "Usage: $0 [environment] [command]"
        exit 1
    fi
}

# Function to check if Docker is running
check_docker() {
    if ! docker info >/dev/null 2>&1; then
        print_error "Docker is not running or not accessible."
        print_error "Please start Docker and try again."
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
        print_success "Environment variables loaded from .env file"
    else
        print_warning "No .env file found at: $env_file"
    fi
    
}

# Function to initialize git submodules before Docker build
init_submodules() {
    cd "$PROJECT_DIR"
    
    print_status "Initializing git submodules..."
    
    # Use the submodule script (similar to install.sh approach)
    if [ -f "$PROJECT_DIR/scripts/submodule-init.sh" ]; then
        print_status "Using submodule-init.sh script..."
        bash "$PROJECT_DIR/scripts/submodule-init.sh"
        return $?
    else
        print_warning "submodule-init.sh not found, falling back to manual initialization..."
        # Fallback to manual approach
        if [ ! -d "ehr_common/.git" ] || [ ! -d "protos/ehr_protos/.git" ]; then
            git submodule init 2>/dev/null || true
            git submodule update --init --recursive 2>/dev/null || return 1
        else
            git submodule update --init --recursive 2>/dev/null || return 1
        fi
        return 0
    fi
}

# Function to start services
start() {
    cd "$PROJECT_DIR"
    
    # Initialize git submodules BEFORE building Docker images
    # This ensures submodules are available in the Docker build context
    if ! init_submodules; then
        print_error "Submodule initialization failed. Cannot proceed with Docker build."
        print_error "Please run: make submodule-init && make submodule-update"
        exit 1
    fi
    
    print_status "Building images with BuildKit cache..."
    export DOCKER_BUILDKIT=1
    export COMPOSE_DOCKER_CLI_BUILD=1
    docker compose -p "$PROJECT_NAME" -f "$COMPOSE_FILE" build --parallel --progress=plain
    
    print_status "Pulling external images..."
    docker compose -p "$PROJECT_NAME" -f "$COMPOSE_FILE" pull --ignore-build-pending || print_warning "Some external images may not be available"
    
    print_status "Starting services..."
    docker compose -p "$PROJECT_NAME" -f "$COMPOSE_FILE" up -d
    
    print_success "Services started"
    
    docker compose -p "$PROJECT_NAME" -f "$COMPOSE_FILE" ps
}

# Function to stop services
stop() {
    print_status "Stopping services..."
    cd "$PROJECT_DIR"
    docker compose -p "$PROJECT_NAME" -f "$COMPOSE_FILE" down --remove-orphans
    print_success "Services stopped"
}

# Function to restart services
restart() {
    print_status "Restarting services..."
    stop
    start
}

# Function to show service status
ps() {
    cd "$PROJECT_DIR"
    docker compose -p "$PROJECT_NAME" -f "$COMPOSE_FILE" ps
}

# Function to deploy with Jenkins-style environment handling
deploy() {
    # Jenkins-friendly deploy flow
    cd "$PROJECT_DIR"

    if [[ -n "${ENV_SRC:-}" ]]; then
        cp "${ENV_SRC}" .env || { print_error "Failed to copy ENV_SRC to .env"; exit 1; }
        print_success "Copied app env from ${ENV_SRC}"
    else
        print_warning "ENV_SRC not provided; skipping app .env copy"
    fi

    # Speed up builds and caching
    export DOCKER_BUILDKIT=1
    export COMPOSE_DOCKER_CLI_BUILD=1

    # Compose optional env flag
    compose_env_args=()
    if [[ -f .env ]]; then
        compose_env_args+=(--env-file .env)
    fi

    docker compose -p "$PROJECT_NAME" "${compose_env_args[@]}" -f "$COMPOSE_FILE" down --remove-orphans || true

    CURRENT_COMMIT=$(git rev-parse HEAD)
    IMAGE_NAME="ehr_gateway_prod:latest"

    if docker image inspect "$IMAGE_NAME" >/dev/null 2>&1; then
        if docker image inspect "$IMAGE_NAME" | grep -q "$CURRENT_COMMIT" 2>/dev/null; then
            print_success "Image is up-to-date with current commit. Skipping rebuild."
            REBUILD_NEEDED=false
        else
            print_status "Code has changed. Rebuilding image..."
            REBUILD_NEEDED=true
        fi
    else
        print_status "Image doesn't exist. Building for the first time..."
        REBUILD_NEEDED=true
    fi

    if [ "$REBUILD_NEEDED" = true ]; then
        # Initialize git submodules BEFORE building Docker images
        if ! init_submodules; then
            print_error "Submodule initialization failed. Cannot proceed with Docker build."
            print_error "Please run: make submodule-init && make submodule-update"
            exit 1
        fi
        
        print_status "Building Docker images..."
        docker compose -p "$PROJECT_NAME" "${compose_env_args[@]}" -f "$COMPOSE_FILE" build --progress=plain --parallel
        
        docker tag "$IMAGE_NAME" "${IMAGE_NAME%:latest}:${CURRENT_COMMIT}"
        print_success "Image built and tagged with commit: $CURRENT_COMMIT"
    else
        print_success "Using existing image. No rebuild needed."
    fi

    docker image prune -f || true

    print_status "Starting containers..."
    docker compose -p "$PROJECT_NAME" "${compose_env_args[@]}" -f "$COMPOSE_FILE" up -d

    docker compose -p "$PROJECT_NAME" "${compose_env_args[@]}" -f "$COMPOSE_FILE" ps
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
            print_error "Unknown command: $COMMAND"
            print_error "Available commands: up, down, restart, ps, deploy"
            usage
            exit 1
            ;;
    esac
}

# Run main function
main "$@"