# ==============================================================================
# Project Setup
# ==============================================================================

PROJECT_NAME := django_template
PYTHON       := uv run python
# Only DJANGO_APP_PORT for `make run` (not PORT / APP_PORT — those are deploy-only).
# Do not `-include .env` — Make mangles # $ quotes.
# Use := so project .env beats stale IDE-exported values ( ?= would keep env).
# CLI still wins: make run DJANGO_APP_PORT=8100
_DJANGO_APP_PORT_FROM_ENV := $(shell sed -n 's/^DJANGO_APP_PORT=//p' .env 2>/dev/null | tr -d '"[:space:]' | head -n1)
DJANGO_APP_PORT := $(or $(_DJANGO_APP_PORT_FROM_ENV),8000)
# Back-compat for makefiles that still use DJANGO_PORT.
DJANGO_PORT  := $(DJANGO_APP_PORT)
ROOT         := $(shell git rev-parse --show-toplevel 2>/dev/null || echo "..")
MANAGE       := $(PYTHON) manage.py
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
include deploy/Makefile

.PHONY: infra-up infra-up-scanning infra-down deploy-seed

infra-up: ## Start Django Template infra (postgres redis rabbitmq mailpit minio)
	@$(MAKE) -C infra up

infra-up-scanning: ## Start Django Template infra + ClamAV (virus scan on upload)
	@$(MAKE) -C infra up-scanning

infra-down: ## Stop infra stack
	@$(MAKE) -C infra down

deploy-seed: ## Run load_superusers via deploy tools container
	@$(MAKE) -C . -f deploy/Makefile seed
