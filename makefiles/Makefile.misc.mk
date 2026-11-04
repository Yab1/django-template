# ==============================================================================
# Git hooks (pre-push: block direct push to main)
# ==============================================================================
.PHONY: install-hooks

install-hooks: ## Use repo .githooks (pre-commit lint gate; pre-push blocks main)
	$(call title,Configuring Git hooks path)
	git config core.hooksPath .githooks
	@chmod +x .githooks/pre-push .githooks/pre-commit
	$(call ok,Git will use .githooks/ (pre-commit lint; pre-push blocks main; run 'make precommit' for hook envs))

# ==============================================================================
# Dependency / security audit
# ==============================================================================
.PHONY: audit

audit: ## Run pip-audit to check dependencies for known vulnerabilities
	$(call title,Auditing dependencies for known vulnerabilities)
	uv run --extra dev pip-audit
	$(call ok,No known vulnerabilities found)

# ==============================================================================
# Miscellaneous
# ==============================================================================
.PHONY: clean-migrations format lint lint-check demo-logging create-app loaddata loaddata-all sync-rules rename-project remove-cookbook

sync-rules: ## Regenerate .codex/ and .claude/ from .cursor/rules/
	$(call title,Syncing agent rules from .cursor/rules)
	$(PYTHON) scripts/sync_from_cursor_rules.py
	$(call ok,Agent rules synced)

clean-migrations: ## Remove migration files
	find core -path "*/migrations/*.py" -not -name "__init__.py" -delete
	find core -path "*/migrations/*.pyc" -delete
	$(call ok,Migrations cleaned)

format: ## Format code with ruff
	$(call title,Formatting code)
	uv run --extra dev ruff format .
	$(call ok,Code formatted)

lint: format ## Run linters (includes formatting)
	$(call title,Running linters)
	@echo "Running ruff check on all Python files..."
	uv run --extra dev ruff check . --fix
	@echo "Running other pre-commit hooks..."
	uv run --extra dev pre-commit run --all-files check-yaml
	uv run --extra dev pre-commit run --all-files check-added-large-files
	$(call ok,Linting complete)

lint-check: ## Lint without writing (CI / branch protection)
	$(call title,Checking lint (no writes))
	uv run --extra dev ruff format --check .
	uv run --extra dev ruff check --no-fix .
	uv run --extra dev pre-commit run --all-files check-yaml
	uv run --extra dev pre-commit run --all-files check-added-large-files
	$(call ok,Lint check passed)

create-app: ## Create Django app with optional registration (APP=<name>)
	@if [ -z "$(APP)" ]; then echo "Usage: make create-app APP=<app_name>"; exit 2; fi
	$(MANAGE) create_app $(APP) $(if $(REGISTER),--register,)

rename-project: ## Rename template identity (SNAKE= KEBAB= NAME= PREFIX=) [DRY_RUN=1]
	@if [ -z "$(SNAKE)" ] || [ -z "$(KEBAB)" ] || [ -z "$(NAME)" ] || [ -z "$(PREFIX)" ]; then \
		echo "Usage: make rename-project SNAKE=acme_api KEBAB=acme-api NAME='Acme API' PREFIX=AC [DRY_RUN=1]"; \
		exit 2; \
	fi
	@bash ./scripts/rename_project.sh --snake "$(SNAKE)" --kebab "$(KEBAB)" --name "$(NAME)" --prefix "$(PREFIX)" $(if $(DRY_RUN),--dry-run,)

remove-cookbook: ## Delete core.cookbook specimen + wiring [DRY_RUN=1]
	@bash ./scripts/remove_cookbook.sh $(if $(DRY_RUN),--dry-run,)

