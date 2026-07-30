# ==============================================================================
# Django Management
# ==============================================================================
.PHONY: run migrate makemigrate dry-migrate shell superuser seed-superuser collectstatic flush seed-patients django-check migrations

# ==============================================================================
# Server & Development
# ==============================================================================
run: ## Run Django server
	$(call title,Running server on DJANGO_PORT $(DJANGO_PORT))
	$(MANAGE) runserver $(DJANGO_PORT)

shell: ## Open Django shell
	$(MANAGE) shell

django-check: ## Check Django health and perform checks
	$(MANAGE) check

# ==============================================================================
# Migrations
# ==============================================================================
migrations: ## Create migrations
	$(MANAGE) makemigrations

migrate: ## Apply migrations
	$(MANAGE) migrate

makemigrate: ## Create and apply migrations
	$(MANAGE) makemigrations
	$(MANAGE) migrate

dry-migrate: ## Dry run migrations
	$(MANAGE) makemigrations --dry-run 2>&1 | head -20

# ==============================================================================
# Database Management
# ==============================================================================
flush: ## Flush database
	$(MANAGE) flush --noinput

seed-patients: ## Seed patient data (COUNT=10, use --clear to clear existing)
	$(call title,Seeding patients)
	$(MANAGE) seed_patients --count $(or $(COUNT),10) $(if $(CLEAR),--clear,)

# ==============================================================================
# User Management
# ==============================================================================
superuser: ## Create superuser
	$(MANAGE) createsuperuser

seed-superuser: ## Load superusers from YAML secrets file (use --update to update existing)
	$(call title,Loading superusers from secrets file)
	$(MANAGE) load_superusers $(if $(UPDATE),--update,)

# ==============================================================================
# Static Files
# ==============================================================================
collectstatic: ## Collect static files
	$(MANAGE) collectstatic --noinput

