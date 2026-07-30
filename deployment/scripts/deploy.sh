#!/bin/bash
# Blue-green Docker deploy: new slot becomes healthy before traffic switches; old slot stops after.
# Nginx Proxy Manager should keep forwarding to host port 7000 (ehr_backend_proxy).

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/load-config.sh"

DEPLOY_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
ACTIVE_SLOT_FILE="$DEPLOY_DIR/.active-slot"
NGINX_TEMPLATE="$DEPLOY_DIR/nginx/app-active.conf.template"
NGINX_ACTIVE="$DEPLOY_DIR/nginx/app-active.conf"
HEALTH_PATH="/api/v1/systems/health-check/"
# Printed by deployment/entrypoint.sh immediately before `exec gunicorn` (after migrate + collectstatic).
ENTRYPOINT_GUNICORN_MARKER="${ENTRYPOINT_GUNICORN_MARKER:-ehr-backend-entrypoint: ready-for-gunicorn}"

# Active slot is inferred from running containers so a clean Jenkins workspace still deploys correctly.
# If both slots are up (e.g. failed mid-deploy), prefer the upstream chosen in ehr_backend_proxy.
# Uses printf -v so we never rely on $(...) (subshell would swallow exit 1).
infer_active_slot_into() {
    local _outvar="$1"
    local blue_up=false green_up=false
    docker ps --format '{{.Names}}' | grep -Fxq 'ehr_backend_blue' && blue_up=true
    docker ps --format '{{.Names}}' | grep -Fxq 'ehr_backend_green' && green_up=true

    if $blue_up && $green_up; then
        local upstream=""
        if docker ps --format '{{.Names}}' | grep -Fxq 'ehr_backend_proxy'; then
            upstream=$(docker exec ehr_backend_proxy sh -c \
                "grep -oE 'ehr_backend_(blue|green)' /etc/nginx/conf.d/default.conf 2>/dev/null | head -1" \
                || true)
        fi
        case "$upstream" in
            ehr_backend_blue)
                log_info "Both slots running; active=blue (from ehr_backend_proxy). Deploy will reconcile."
                printf -v "$_outvar" '%s' 'blue'
                return 0
                ;;
            ehr_backend_green)
                log_info "Both slots running; active=green (from ehr_backend_proxy). Deploy will reconcile."
                printf -v "$_outvar" '%s' 'green'
                return 0
                ;;
            *)
                log_error "Both ehr_backend_blue and ehr_backend_green are running; could not read active upstream from ehr_backend_proxy. Stop one container, then retry."
                exit 1
                ;;
        esac
    fi
    if $blue_up; then
        printf -v "$_outvar" '%s' 'blue'
        return 0
    fi
    if $green_up; then
        printf -v "$_outvar" '%s' 'green'
        return 0
    fi
    printf -v "$_outvar" '%s' ''
}

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${BLUE}$1${NC}"; }
log_success() { echo -e "${GREEN}$1${NC}"; }
log_error() { echo -e "${RED}$1${NC}" >&2; }

docker_compose() {
    docker compose "$@" 2> >(grep -vE 'The "[^"]*" variable is not set|Docker Compose is configured to build using Bake' >&2)
}

check_docker() {
    if ! docker info >/dev/null 2>&1; then
        log_error "Docker is not running"
        exit 1
    fi
}

check_compose_file() {
    if [[ ! -f "$COMPOSE_FILE" ]]; then
        log_error "Compose file not found: $COMPOSE_FILE"
        exit 1
    fi
}

check_nginx_template() {
    if [[ ! -f "$NGINX_TEMPLATE" ]]; then
        log_error "Nginx template not found: $NGINX_TEMPLATE"
        exit 1
    fi
}

has_submodules() {
    cd "$PROJECT_DIR"
    [ -f ".gitmodules" ] || git submodule status 2>/dev/null | grep -q .
}

init_submodules() {
    cd "$PROJECT_DIR"

    if ! has_submodules; then
        return 0
    fi

    log_info "Initializing git submodules..."

    if [ -f "$PROJECT_DIR/scripts/submodule-init.sh" ]; then
        bash "$PROJECT_DIR/scripts/submodule-init.sh"
    else
        git submodule init 2>/dev/null || true
        git submodule update --init --recursive 2>/dev/null
    fi
}

write_nginx_upstream() {
    local backend_host="$1"
    sed "s/__BACKEND_HOST__/${backend_host}/" "$NGINX_TEMPLATE" >"${NGINX_ACTIVE}.new"
    mv "${NGINX_ACTIVE}.new" "$NGINX_ACTIVE"
}

# Bind-mount path is fixed when the container is created. Jenkins often uses a new workspace path
# each build, so `nginx -s reload` would still read the OLD file. Recreate the proxy so the mount
# points at this checkout's deployment/nginx/app-active.conf.
recreate_ehr_backend_proxy() {
    log_info "Recreating ehr_backend_proxy (refresh bind-mount to this workspace's nginx config)..."
    docker_compose -f "$COMPOSE_FILE" "${compose_env_args[@]}" up -d --no-deps --force-recreate ehr_backend_proxy
}

ensure_background_workers() {
    log_info "Starting/recreating background workers (celery, beat, temporal)..."
    docker_compose -f "$COMPOSE_FILE" "${compose_env_args[@]}" up -d --no-deps --force-recreate \
        ehr_backend_celery ehr_backend_celery_beat ehr_backend_temporal_worker
}

wait_proxy_healthy() {
    local max_wait="${PROXY_HEALTH_WAIT_SECONDS:-90}"
    local elapsed=0

    log_info "Waiting for traffic via ehr_backend_proxy on :7000 (${HEALTH_PATH})..."
    while [ "$elapsed" -lt "$max_wait" ]; do
        if command -v curl >/dev/null 2>&1; then
            if curl -sfS "http://127.0.0.1:7000${HEALTH_PATH}" >/dev/null; then
                log_success "Proxy -> Django health OK"
                return 0
            fi
        elif command -v wget >/dev/null 2>&1; then
            if wget -qO- "http://127.0.0.1:7000${HEALTH_PATH}" >/dev/null 2>&1; then
                log_success "Proxy -> Django health OK"
                return 0
            fi
        else
            log_error "Need curl or wget on the deploy host to verify :7000"
            return 1
        fi
        sleep 2
        elapsed=$((elapsed + 2))
    done
    log_error "Proxy health check failed within ${max_wait}s (502 upstream? wrong bind-mount path?)"
    return 1
}

docker_container_restart_count() {
    local name="$1"
    local n
    n=$(docker inspect -f '{{.RestartCount}}' "$name" 2>/dev/null) || return 1
    # Numeric only (empty or non-numeric → 0)
    if [[ "$n" =~ ^[0-9]+$ ]]; then
        echo "$n"
    else
        echo "0"
    fi
}

# Gunicorn is not listening until migrate + collectstatic finish; HTTP health would fail for minutes on large
# migrations. Wait for the entrypoint log line that precedes `exec gunicorn`, then probe health.
wait_entrypoint_reached_gunicorn() {
    local slot="$1"
    local svc="ehr_backend_${slot}"
    local max_wait="${ENTRYPOINT_SERVER_WAIT_SECONDS:-3600}"
    local elapsed=0

    log_info "Waiting for ${svc} to finish migrations/collectstatic (max ${max_wait}s, then HTTP health)..."
    while [ "$elapsed" -lt "$max_wait" ]; do
        if ! docker ps --format '{{.Names}}' | grep -Fxq "$svc"; then
            log_error "${svc} is not running — entrypoint may have failed. Last logs:"
            docker logs --tail 80 "$svc" 2>&1 || true
            return 1
        fi
        if docker logs --tail 250 "$svc" 2>&1 | grep -qF "$ENTRYPOINT_GUNICORN_MARKER"; then
            log_success "${svc} reached application server startup (migrations/collectstatic done)"
            return 0
        fi
        if [ "$elapsed" -gt 0 ] && [ $((elapsed % 30)) -eq 0 ]; then
            log_info "Still waiting for ${svc} (migrations or collectstatic may still be running)..."
        fi
        sleep 3
        elapsed=$((elapsed + 3))
    done
    log_error "${svc}: timed out before Gunicorn start after ${max_wait}s. Last logs:"
    docker logs --tail 120 "$svc" 2>&1 || true
    return 1
}

wait_healthy() {
    local slot="$1"
    local svc="ehr_backend_${slot}"
    local max_wait="${HEALTH_WAIT_SECONDS:-120}"
    local elapsed=0

    if ! wait_entrypoint_reached_gunicorn "$slot"; then
        return 1
    fi

    local restarts_at_health_start
    restarts_at_health_start=$(docker_container_restart_count "$svc")
    restarts_at_health_start=${restarts_at_health_start:-0}

    log_info "Waiting for ${svc} health (${HEALTH_PATH})..."
    while [ "$elapsed" -lt "$max_wait" ]; do
        if ! docker ps --format '{{.Names}}' | grep -Fxq "$svc"; then
            log_error "${svc} stopped during health check. Last logs:"
            docker logs --tail 100 "$svc" 2>&1 || true
            return 1
        fi
        local restarts_now
        restarts_now=$(docker_container_restart_count "$svc")
        restarts_now=${restarts_now:-0}
        if [ "$restarts_now" -gt "$restarts_at_health_start" ]; then
            log_error "${svc} restarted while waiting for health (process crash / exit). Last logs:"
            docker logs --tail 120 "$svc" 2>&1 || true
            return 1
        fi
        if docker_compose -f "$COMPOSE_FILE" "${compose_env_args[@]}" exec -T "$svc" .venv/bin/python -c \
            "import urllib.request; urllib.request.urlopen('http://127.0.0.1:7000${HEALTH_PATH}').read()" \
            2>/dev/null; then
            log_success "${svc} is healthy"
            return 0
        fi
        sleep 2
        elapsed=$((elapsed + 2))
    done
    log_error "${svc} failed health check within ${max_wait}s (no HTTP response; if the app crash-loops, RestartCount should have been detected — check docker logs)"
    docker logs --tail 80 "$svc" 2>&1 || true
    return 1
}

remove_legacy_container() {
    if docker ps -a --format '{{.Names}}' | grep -qx 'ehr_backend'; then
        log_info "Removing legacy container ehr_backend (use blue/green + ehr_backend_proxy on :7000)..."
        docker rm -f ehr_backend 2>/dev/null || true
    fi
}

deploy() {
    cd "$PROJECT_DIR" || exit 1

    export DOCKER_BUILDKIT=1
    export COMPOSE_DOCKER_CLI_BUILD=1
    export DOCKER_BUILD_CONTEXT="$PROJECT_DIR"

    compose_env_args=()
    [[ -f .env ]] && compose_env_args+=(--env-file .env)

    remove_legacy_container

    CURRENT_COMMIT=$(git rev-parse HEAD 2>/dev/null || echo "unknown")

    if ! init_submodules; then
        log_error "Submodule initialization failed"
        exit 1
    fi

    log_info "Building Docker images..."
    docker_compose -f "$COMPOSE_FILE" "${compose_env_args[@]}" build --parallel ehr_backend_blue

    if [ "$CURRENT_COMMIT" != "unknown" ]; then
        docker tag "$IMAGE_NAME" "${IMAGE_NAME%:latest}:${CURRENT_COMMIT}" 2>/dev/null || true
    fi

    docker image prune -f || true

    local active_slot
    infer_active_slot_into active_slot

    if [[ -z "$active_slot" ]]; then
        log_info "Cold start: active slot=blue, proxy -> ehr_backend_blue:7000"
        write_nginx_upstream "ehr_backend_blue"
        log_info "Starting ehr_backend_blue..."
        docker_compose -f "$COMPOSE_FILE" "${compose_env_args[@]}" up -d ehr_backend_blue
        if ! wait_healthy blue; then
            exit 1
        fi
        recreate_ehr_backend_proxy
        if ! wait_proxy_healthy; then
            exit 1
        fi
        echo "blue" >"$ACTIVE_SLOT_FILE"
        ensure_background_workers
        docker_compose -f "$COMPOSE_FILE" "${compose_env_args[@]}" ps
        log_success "Cold deploy complete (NPM -> host:7000 -> blue)"
        return 0
    fi

    local old_slot="$active_slot"
    local new_slot
    if [[ "$active_slot" == "blue" ]]; then
        new_slot=green
    else
        new_slot=blue
    fi

    log_info "Blue-green: bringing up inactive slot ${new_slot} (traffic still on ${old_slot})..."
    docker_compose -f "$COMPOSE_FILE" "${compose_env_args[@]}" up -d "ehr_backend_${new_slot}"

    if ! wait_healthy "$new_slot"; then
        exit 1
    fi

    log_info "Switching proxy to ehr_backend_${new_slot}..."
    write_nginx_upstream "ehr_backend_${new_slot}"
    recreate_ehr_backend_proxy
    if ! wait_proxy_healthy; then
        log_error "Aborting before stopping ${old_slot}: fix nginx/proxy, then redeploy."
        exit 1
    fi

    log_info "Stopping previous slot ehr_backend_${old_slot}..."
    docker_compose -f "$COMPOSE_FILE" "${compose_env_args[@]}" stop "ehr_backend_${old_slot}" || true

    echo "$new_slot" >"$ACTIVE_SLOT_FILE"
    ensure_background_workers
    docker_compose -f "$COMPOSE_FILE" "${compose_env_args[@]}" ps
    log_success "Deploy complete; active=${new_slot} (NPM -> host:7000)"
}

main() {
    log_info "======================================="
    log_info "DEPLOYMENT (blue-green)"
    log_info "======================================="

    cd "$PROJECT_DIR" || exit 1

    if [ -f .env ]; then
        set -a
        # shellcheck disable=SC1091
        source .env
        set +a
    else
        log_error ".env file not found"
        exit 1
    fi

    check_docker
    check_compose_file
    check_nginx_template
    deploy

    log_info "======================================="
    log_success "DEPLOYMENT COMPLETE"
    log_info "======================================="
}

main "$@"
