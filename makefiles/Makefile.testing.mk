# ==============================================================================
# Testing
# ==============================================================================
.PHONY: test test-cov test-html test-xml test-fast test-watch test-app test-models test-services test-mutations test-queries test-unit test-integration test-create-db pytest open-coverage

test: ## Run all tests
	$(call title,Running all tests)
	uv run python -m pytest

test-cov: ## Run tests with coverage report
	$(call title,Running tests with coverage)
	uv run python -m pytest --cov=core --cov-report=term-missing

test-html: ## Run tests with HTML coverage report
	$(call title,Running tests with HTML coverage report)
	uv run python -m pytest --cov=core --cov-report=html --cov-report=term-missing
	$(call ok,Coverage report generated in htmlcov/index.html)

test-xml: ## Run tests with XML coverage report (for CI)
	$(call title,Running tests with XML coverage report)
	uv run python -m pytest --cov=core --cov-report=xml --cov-report=term-missing

test-fast: ## Run tests without coverage (faster)
	$(call title,Running tests without coverage)
	uv run python -m pytest --no-cov

test-watch: ## Run tests in watch mode (requires pytest-watch)
	$(call title,Running tests in watch mode)
	uv run ptw -- --cov=core --cov-report=term-missing

test-app: ## Run tests for specific app (APP=patients|fhir|users)
	@if [ -z "$(APP)" ]; then echo "Usage: make test-app APP=<app_name>"; exit 2; fi
	$(call title,Running tests for app: $(APP))
	uv run python -m pytest core/$(APP)/tests/ --cov=core.$(APP) --cov-report=term-missing

test-models: ## Run model tests only
	$(call title,Running model tests)
	uv run python -m pytest core/*/tests/models/ --cov=core --cov-report=term-missing

test-services: ## Run service tests only
	$(call title,Running service tests)
	uv run python -m pytest core/*/tests/services/ --cov=core --cov-report=term-missing

test-mutations: ## Run mutation tests only
	$(call title,Running mutation tests)
	uv run python -m pytest core/*/tests/mutations/ --cov=core --cov-report=term-missing

test-queries: ## Run query tests only
	$(call title,Running query tests)
	uv run python -m pytest core/*/tests/queries/ --cov=core --cov-report=term-missing

test-unit: ## Run unit tests (marked with @pytest.mark.unit)
	$(call title,Running unit tests)
	uv run python -m pytest -m unit --cov=core --cov-report=term-missing

test-integration: ## Run integration tests (marked with @pytest.mark.integration)
	$(call title,Running integration tests)
	uv run python -m pytest -m integration --cov=core --cov-report=term-missing

test-create-db: ## Recreate pytest DB after migrations (ARGS= optional paths, e.g. ARGS="core/lab/tests/ -q")
	$(call title,Recreating pytest database and running tests)
	uv run python -m pytest --create-db $(ARGS)

pytest: test-cov ## Alias for test-cov (backward compatibility)

open-coverage: ## Open coverage report
	open htmlcov/index.html

