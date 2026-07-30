# ==============================================================================
# Deployment Orchestration
# ==============================================================================
.PHONY: up down restart ps deploy help

help: ## Show this help message
	@echo "Usage: make [target]"
	@echo ""
	@echo "Targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-15s %s\n", $$1, $$2}'

up: ## Start services
	@./deployment/docker-orchestrate.sh up

down: ## Stop services
	@./deployment/docker-orchestrate.sh down

restart: ## Restart services
	@./deployment/docker-orchestrate.sh restart

ps: ## Show service status
	@./deployment/docker-orchestrate.sh ps

deploy: ## Deploy with optimized build and caching
	@./deployment/docker-orchestrate.sh deploy

