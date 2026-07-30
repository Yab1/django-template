# ==============================================================================
# Git hooks (pre-push: block direct push to main)
# ==============================================================================
.PHONY: install-hooks

install-hooks: ## Use repo .githooks (pre-push blocks push to main)
	$(call title,Configuring Git hooks path)
	git config core.hooksPath .githooks
	$(call ok,Git will use .githooks/ (run 'make precommit' for pre-commit hooks))

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
.PHONY: clean-migrations format lint demo-logging create-app loaddata loaddata-all sync-rules

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

create-app: ## Create Django app with optional registration (APP=<name>)
	@if [ -z "$(APP)" ]; then echo "Usage: make create-app APP=<app_name>"; exit 2; fi
	$(MANAGE) create_app $(APP) $(if $(REGISTER),--register,)

