# ==============================================================================
# Deployment Orchestration
# ==============================================================================
.PHONY: start stop restart status deploy

start: ## Start services
	@./deployment/scripts/orchestrate.sh start

stop: ## Stop services
	@./deployment/scripts/orchestrate.sh stop

restart: ## Restart services
	@./deployment/scripts/orchestrate.sh restart

status: ## Show service status
	@./deployment/scripts/orchestrate.sh status

deploy: ## Deploy with optimized build and caching
	@./deployment/scripts/deploy.sh

