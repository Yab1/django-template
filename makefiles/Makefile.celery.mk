# ==============================================================================
# Celery
# ==============================================================================
.PHONY: celery celery-beat celery-all

celery: ## Run Celery worker
	uv run celery -A config.settings.celery worker --loglevel=info --pool=solo

celery-beat: ## Run Celery beat
	uv run celery -A config.settings.celery beat --loglevel=info

celery-all: ## Run Celery worker + beat
	uv run celery -A config.settings.celery worker --loglevel=info --pool=solo --beat

