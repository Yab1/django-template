# ==============================================================================
# Miscellaneous
# ==============================================================================
.PHONY: clean-migrations format lint demo-logging create-app loaddata loaddata-all

clean-migrations: ## Remove migration files
	find core -path "*/migrations/*.py" -not -name "__init__.py" -delete
	find core -path "*/migrations/*.pyc" -delete
	$(call ok,Migrations cleaned)

format: ## Format code with ruff
	$(call title,Formatting code)
	uv run ruff format .
	$(call ok,Code formatted)

lint: format ## Run linters (includes formatting)
	$(call title,Running linters)
	@echo "Running ruff check on all Python files..."
	uv run ruff check . --fix
	@echo "Running other pre-commit hooks..."
	uv run pre-commit run --all-files check-yaml
	uv run pre-commit run --all-files check-added-large-files
	$(call ok,Linting complete)

demo-logging: ## Demonstrate enhanced Rich logging features
	$(call title,Running Rich logging demo)
	$(PYTHON) scripts/demo_rich_logging.py
	$(call ok,Demo complete)

create-app: ## Create Django app with optional registration (APP=<name>)
	@if [ -z "$(APP)" ]; then echo "Usage: make create-app APP=<app_name>"; exit 2; fi
	$(MANAGE) create_app $(APP) $(if $(REGISTER),--register,)

loaddata: ## Load specific fixture(s)
	$(call title,Loading fixture: $(filter-out $@,$(MAKECMDGOALS)))
	$(MANAGE) loaddata $(filter-out $@,$(MAKECMDGOALS))

loaddata-all: ## Load all fixtures in dependency order (supports any nesting depth)
	@echo "Loading fixtures in dependency order..."
	@echo "Step 1: Loading all coding fixtures..."
	@fixtures=$$(find core -type f \( -name "coding.yaml" -o -name "coding.json" \) -path "*/fixtures/*" | \
		while read f; do echo "$$f" | sed 's|\.yaml$$||' | sed 's|\.json$$||'; done | \
		sort | tr '\n' ' '); \
	if [ -n "$$fixtures" ]; then \
		$(MANAGE) loaddata $$fixtures; \
	fi
	@echo "Step 2: Loading all codeable_concept fixtures..."
	@fixtures=$$(find core -type f \( -name "codeable_concept.yaml" -o -name "codeable_concept.json" \) -path "*/fixtures/*" | \
		while read f; do echo "$$f" | sed 's|\.yaml$$||' | sed 's|\.json$$||'; done | \
		sort | tr '\n' ' '); \
	if [ -n "$$fixtures" ]; then \
		$(MANAGE) loaddata $$fixtures; \
	fi
	@echo "Step 3: Loading all codeable_reference fixtures..."
	@fixtures=$$(find core -type f \( -name "codeable_reference.yaml" -o -name "codeable_reference.json" \) -path "*/fixtures/*" | \
		while read f; do echo "$$f" | sed 's|\.yaml$$||' | sed 's|\.json$$||'; done | \
		sort | tr '\n' ' '); \
	if [ -n "$$fixtures" ]; then \
		$(MANAGE) loaddata $$fixtures; \
	fi
	@echo "All fixtures loaded successfully!"

