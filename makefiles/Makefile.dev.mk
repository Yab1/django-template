# ==============================================================================
# Local dev (Honcho — Django, Celery, Celery Beat)
# ==============================================================================
.PHONY: dev dev-all dev-stop dev-web dev-celery dev-celery-beat

dev: dev-all ## Start Django, Celery, and Celery Beat (honcho)

dev-all: ## Start all local dev processes using honcho (kills any existing processes first)
	$(call title,Starting Django + Celery + Celery Beat)
	@pkill -9 -f "hon[c]ho start" || true
	@pkill -9 -f "config.settings.cele[r]y" || true
	@pkill -9 -f "daph[n]e" || true
	@sleep 2
	uv run honcho start

dev-web: ## Start only Django via honcho
	uv run honcho start web

dev-celery: ## Start only Celery worker via honcho
	uv run honcho start celery

dev-celery-beat: ## Start only Celery beat via honcho
	uv run honcho start celery-beat

dev-stop: ## Stop honcho-managed dev processes
	@pkill -f "honcho start" || true
	$(call ok,Dev processes stopped)
