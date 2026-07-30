# ==============================================================================
# Temporal
# ==============================================================================
.PHONY: temporal

temporal: ## Run Temporal worker
	$(PYTHON) -m core.workflows.temporal.worker
