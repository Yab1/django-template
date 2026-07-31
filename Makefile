# ==============================================================================
# Project Setup
# ==============================================================================

PROJECT_NAME := django_template
PYTHON       := uv run python
DJANGO_PORT  := 8000
ROOT         := $(shell git rev-parse --show-toplevel 2>/dev/null || echo "..")
DEV_DOCKER   := $(shell grep -E '^DJANGO_DEV_DOCKER=' .env 2>/dev/null | cut -d= -f2)
ifeq ($(DEV_DOCKER),1)
MANAGE       := cd $(ROOT) && docker compose -f development/docker-compose.yml exec django_template_dev python manage.py
else
MANAGE       := $(PYTHON) manage.py
endif
COLOR_RESET  := \033[0m
COLOR_BLUE   := \033[1;34m
COLOR_GREEN  := \033[1;32m
COLOR_YELLOW := \033[1;33m

define title
	@echo "$(COLOR_BLUE)==>$(COLOR_RESET) $(1)"
endef

define ok
	@echo "$(COLOR_GREEN)✔$(COLOR_RESET) $(1)"
endef

# ==============================================================================
# Help
# ==============================================================================
.PHONY: help
help:
	@echo ""
	@echo "$(COLOR_YELLOW)Available commands:$(COLOR_RESET)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
	awk 'BEGIN {FS = ":.*?## "}; {printf "  $(COLOR_GREEN)%-25s$(COLOR_RESET) %s\n", $$1, $$2}'
	@echo ""

# ==============================================================================
# Environment
# ==============================================================================
.PHONY: install precommit update

install: ## Install all dependencies (dev + prod) using uv
	$(call title,Installing all dependencies with uv)
	@bash ./scripts/install.sh
	$(call ok,Dependencies installed)

precommit: install-hooks ## Install and configure pre-commit hooks + Git hooks path
	$(call title,Setting up pre-commit)
	uv run --extra dev pre-commit install-hooks
	@chmod +x .githooks/pre-commit
	$(call ok,Pre-commit hooks installed (via .githooks/))

update: install migrate precommit ## Full project update
	$(call ok,Project updated successfully)


# ==============================================================================
# Include Module Makefiles
# ==============================================================================
include makefiles/Makefile.git.mk
include makefiles/Makefile.django.mk
include makefiles/Makefile.dev.mk
include makefiles/Makefile.seed.mk
include makefiles/Makefile.celery.mk
include makefiles/Makefile.misc.mk
include makefiles/Makefile.testing.mk
include makefiles/Makefile.submodules.mk
include makefiles/Makefile.graphify.mk
include deployment/Makefile
