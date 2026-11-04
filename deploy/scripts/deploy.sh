#!/bin/bash
# Blue-green API deploy. New slot healthy before traffic switches; old slot stops after.
# Migrations run once as a one-shot container. API/worker never migrate.
# Seed is a separate script (deploy/scripts/seed.sh).

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
source "$SCRIPT_DIR/load-config.sh"

DEPLOY_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
ACTIVE_SLOT_FILE="$DEPLOY_DIR/.active-slot"
NGINX_TEMPLATE="$DEPLOY_DIR/nginx/app-active.conf.template"
NGINX_ACTIVE="$DEPLOY_DIR/nginx/app-active.conf"
HEALTH_PATH="/health/"
SKIP_MIGRATE=false
ENTRYPOINT_GUNICORN_MARKER="${ENTRYPOINT_GUNICORN_MARKER:-django-template-entrypoint: ready-for-gunicorn}"

while [[ $# -gt 0 ]]; do
    case "$1" in
        --skip-migrate) SKIP_MIGRATE=true; shift ;;
        -h|--help)
            echo "Usage: $0 [--skip-migrate]"
            exit 0
            ;;
        *)
            echo "unknown flag: $1" >&2
            exit 2
            ;;
    esac
done

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

ensure_docker_networks() {
    local nets=(django_template)
    local net
    for net in "${nets[@]}"; do
        if docker network inspect "$net" >/dev/null 2>&1; then
            log_info "Docker network OK: ${net}"
        else
            log_info "Creating Docker network: ${net}"
            docker network create "$net"
        fi
    done
}

infer_active_slot_into() {
    local _outvar="$1"
    local blue_up=false green_up=false
    docker ps --format '{{.Names}}' | grep -Fxq 'django_template_api_blue' && blue_up=true
    docker ps --format '{{.Names}}' | grep -Fxq 'django_template_api_green' && green_up=true

    if $blue_up && $green_up; then
        local upstream=""
        if docker ps --format '{{.Names}}' | grep -Fxq 'django_template_api_proxy'; then
            upstream=$(docker exec django_template_api_proxy sh -c \
                "grep -oE 'django_template_api_(blue|green)' /etc/nginx/conf.d/default.conf 2>/dev/null | head -1" \
                || true)
        fi
        case "$upstream" in
            django_template_api_blue)
                log_info "Both slots running; active=blue (from proxy)."
                printf -v "$_outvar" '%s' 'blue'
                return 0
                ;;
            django_template_api_green)
                log_info "Both slots running; active=green (from proxy)."
                printf -v "$_outvar" '%s' 'green'
                return 0
                ;;
            *)
                log_error "Both API slots running; could not read active upstream from proxy."
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

write_nginx_upstream() {
    local backend_host="$1"
    sed "s/__BACKEND_HOST__/${backend_host}/" "$NGINX_TEMPLATE" >"${NGINX_ACTIVE}.new"
    mv "${NGINX_ACTIVE}.new" "$NGINX_ACTIVE"
}

recreate_proxy() {
    log_info "Recreating django_template_api_proxy..."
    docker_compose -f "$COMPOSE_FILE" "${compose_env_args[@]}" up -d --no-deps --force-recreate django_template_api_proxy
}

ensure_workers() {
    log_info "Starting/recreating django_template_worker and django_template_beat..."
    docker_compose -f "$COMPOSE_FILE" "${compose_env_args[@]}" up -d --no-deps --force-recreate \
        django_template_worker django_template_beat
}

run_migrate() {
    if [[ "$SKIP_MIGRATE" == "true" ]]; then
        log_info "Skipping migrate (--skip-migrate)"
        return 0
    fi
    log_info "Running one-shot migrate (API/worker never migrate)..."
    docker_compose -f "$COMPOSE_FILE" "${compose_env_args[@]}" --profile tools run --rm --no-deps django_template_migrate
}

prune_old_release_tags() {
    local repo="${IMAGE_NAME%:*}"
    if [[ -z "$repo" || "$repo" == "$IMAGE_NAME" ]]; then
        return 0
    fi

    local -A keep_ids=()
    local id name tag img_id
    local -a containers=(
        django_template_api_blue
        django_template_api_green
        django_template_worker
        django_template_beat
        django_template_migrate
        django_template_seed
    )

    id=$(docker image inspect -f '{{.Id}}' "${repo}:latest" 2>/dev/null || true)
    [[ -n "$id" ]] && keep_ids["$id"]=1

    if [[ -n "${CURRENT_COMMIT:-}" && "$CURRENT_COMMIT" != "unknown" ]]; then
        id=$(docker image inspect -f '{{.Id}}' "${repo}:${CURRENT_COMMIT}" 2>/dev/null || true)
        [[ -n "$id" ]] && keep_ids["$id"]=1
    fi

    for name in "${containers[@]}"; do
        id=$(docker inspect -f '{{.Image}}' "$name" 2>/dev/null || true)
        [[ -n "$id" ]] && keep_ids["$id"]=1
    done

    while IFS=' ' read -r tag img_id; do
        [[ "$tag" =~ ^[0-9a-f]{40}$ ]] || continue
        [[ -n "${keep_ids[$img_id]:-}" ]] && continue
        log_info "Removing old ${repo}:${tag}"
        docker rmi "${repo}:${tag}" >/dev/null || log_info "Kept ${repo}:${tag}"
    done < <(docker images "$repo" --no-trunc --format '{{.Tag}} {{.ID}}' 2>/dev/null || true)
}

wait_proxy_healthy() {
    local max_wait="${PROXY_HEALTH_WAIT_SECONDS:-90}"
    local elapsed=0
    local port="${APP_PORT:-8000}"

    log_info "Waiting for traffic via proxy on :${port}${HEALTH_PATH}..."
    while [ "$elapsed" -lt "$max_wait" ]; do
        if command -v curl >/dev/null 2>&1; then
            if curl -sfS "http://127.0.0.1:${port}${HEALTH_PATH}" >/dev/null; then
                log_success "Proxy -> API /health/ OK"
                return 0
            fi
        elif command -v wget >/dev/null 2>&1; then
            if wget -qO- "http://127.0.0.1:${port}${HEALTH_PATH}" >/dev/null 2>&1; then
                log_success "Proxy -> API /health/ OK"
                return 0
            fi
        else
            log_error "Need curl or wget on the deploy host to verify :${port}"
            return 1
        fi
        sleep 2
        elapsed=$((elapsed + 2))
    done
    log_error "Proxy health check failed within ${max_wait}s"
    return 1
}

docker_container_restart_count() {
    local name="$1"
    local n
    n=$(docker inspect -f '{{.RestartCount}}' "$name" 2>/dev/null) || return 1
    if [[ "$n" =~ ^[0-9]+$ ]]; then
        echo "$n"
    else
        echo "0"
    fi
}

wait_entrypoint_reached_gunicorn() {
    local slot="$1"
    local svc="django_template_api_${slot}"
    local max_wait="${ENTRYPOINT_SERVER_WAIT_SECONDS:-600}"
    local elapsed=0

    log_info "Waiting for ${svc} collectstatic (max ${max_wait}s, then HTTP health)..."
    while [ "$elapsed" -lt "$max_wait" ]; do
        if ! docker ps --format '{{.Names}}' | grep -Fxq "$svc"; then
            log_error "${svc} is not running — entrypoint may have failed. Last logs:"
            docker logs --tail 80 "$svc" 2>&1 || true
            return 1
        fi
        if docker logs --tail 250 "$svc" 2>&1 | grep -qF "$ENTRYPOINT_GUNICORN_MARKER"; then
            log_success "${svc} reached application server startup"
            return 0
        fi
        if [ "$elapsed" -gt 0 ] && [ $((elapsed % 30)) -eq 0 ]; then
            log_info "Still waiting for ${svc} (collectstatic may still be running)..."
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
    local svc="django_template_api_${slot}"
    local max_wait="${HEALTH_WAIT_SECONDS:-120}"
    local elapsed=0

    if ! wait_entrypoint_reached_gunicorn "$slot"; then
        return 1
    fi

    local restarts_at_health_start
    restarts_at_health_start=$(docker_container_restart_count "$svc")
    restarts_at_health_start=${restarts_at_health_start:-0}

    log_info "Waiting for ${svc} ${HEALTH_PATH}..."
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
            log_error "${svc} restarted while waiting for health. Last logs:"
            docker logs --tail 120 "$svc" 2>&1 || true
            return 1
        fi
        if docker_compose -f "$COMPOSE_FILE" "${compose_env_args[@]}" exec -T "$svc" \
            curl -fsS "http://127.0.0.1:8000${HEALTH_PATH}" >/dev/null 2>&1; then
            log_success "${svc} is healthy"
            return 0
        fi
        sleep 2
        elapsed=$((elapsed + 2))
    done
    log_error "${svc} failed health check within ${max_wait}s"
    docker logs --tail 80 "$svc" 2>&1 || true
    return 1
}

deploy() {
    cd "$PROJECT_DIR" || exit 1

    export DOCKER_BUILDKIT=1
    export COMPOSE_DOCKER_CLI_BUILD=1
    export DOCKER_BUILD_CONTEXT="$PROJECT_DIR"
    export IMAGE_NAME="${IMAGE_NAME:-django_template:latest}"

    compose_env_args=()
    [[ -f "$APP_ENV_FILE" ]] && compose_env_args+=(--env-file "$APP_ENV_FILE")

    CURRENT_COMMIT=$(git rev-parse HEAD 2>/dev/null || echo "unknown")

    log_info "Building Docker images..."
    docker_compose -f "$COMPOSE_FILE" "${compose_env_args[@]}" build --parallel django_template_api_blue

    if [ "$CURRENT_COMMIT" != "unknown" ]; then
        docker tag "$IMAGE_NAME" "${IMAGE_NAME%:latest}:${CURRENT_COMMIT}" 2>/dev/null || true
    fi

    run_migrate

    local active_slot
    infer_active_slot_into active_slot

    if [[ -z "$active_slot" ]]; then
        log_info "Cold start: active slot=blue"
        write_nginx_upstream "django_template_api_blue"
        log_info "Starting django_template_api_blue..."
        docker_compose -f "$COMPOSE_FILE" "${compose_env_args[@]}" up -d django_template_api_blue
        if ! wait_healthy blue; then
            exit 1
        fi
        recreate_proxy
        if ! wait_proxy_healthy; then
            exit 1
        fi
        echo "blue" >"$ACTIVE_SLOT_FILE"
        ensure_workers
        prune_old_release_tags
        docker_compose -f "$COMPOSE_FILE" "${compose_env_args[@]}" ps
        log_success "Cold deploy complete (proxy -> blue)"
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
    docker_compose -f "$COMPOSE_FILE" "${compose_env_args[@]}" up -d "django_template_api_${new_slot}"

    if ! wait_healthy "$new_slot"; then
        exit 1
    fi

    log_info "Switching proxy to django_template_api_${new_slot}..."
    write_nginx_upstream "django_template_api_${new_slot}"
    recreate_proxy
    if ! wait_proxy_healthy; then
        log_error "Aborting before stopping ${old_slot}: fix nginx/proxy, then redeploy."
        exit 1
    fi

    log_info "Stopping previous slot django_template_api_${old_slot}..."
    docker_compose -f "$COMPOSE_FILE" "${compose_env_args[@]}" stop "django_template_api_${old_slot}" || true

    echo "$new_slot" >"$ACTIVE_SLOT_FILE"
    ensure_workers
    prune_old_release_tags
    docker_compose -f "$COMPOSE_FILE" "${compose_env_args[@]}" ps
    log_success "Deploy complete; active=${new_slot}"
}

main() {
    log_info "======================================="
    log_info "DEPLOYMENT (blue-green)"
    log_info "======================================="

    cd "$PROJECT_DIR" || exit 1

    if [ -f "$APP_ENV_FILE" ]; then
        set -a
        # shellcheck disable=SC1091
        source "$APP_ENV_FILE"
        set +a
    else
        log_error "deploy/.env not found. Create it (same keys as .env.example; docker hostnames postgres/redis)."
        exit 1
    fi

    check_docker
    check_compose_file
    check_nginx_template
    ensure_docker_networks
    deploy

    log_info "======================================="
    log_success "DEPLOYMENT COMPLETE"
    log_info "======================================="
}

main "$@"
