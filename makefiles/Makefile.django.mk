# ==============================================================================
# Django Management
# ==============================================================================
.PHONY: run migrate makemigrate dry-migrate shell superuser collectstatic flush django-check migrations postman-collection

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
# Postman
# ==============================================================================
postman-collection: ## Generate Postman collection JSON (APP= required; optional: RESOURCE, CATEGORY, OUTPUT, NAME, …)
	@$(if $(APP),,$(error APP= is required. Example: make postman-collection APP=billing RESOURCE=charge_item))
	$(call title,Generating Postman collection for $(APP))
	$(MANAGE) generate_postman_collection $(APP) \
		$(if $(RESOURCE),--resource $(RESOURCE),) \
		$(if $(CATEGORY),--category $(CATEGORY),) \
		$(if $(EXCLUDE_CATEGORY),--exclude-category $(EXCLUDE_CATEGORY),) \
		$(if $(OUTPUT),--output $(OUTPUT),) \
		$(if $(NAME),--name $(NAME),) \
		$(if $(filter true,$(DRY_RUN)),--dry-run,) \
		$(if $(filter true,$(MERGE)),--merge,) \
		$(if $(filter true,$(MANIFEST)),--manifest,) \
		$(if $(filter true,$(SKIP_RESPONSES)),--skip-responses,) \
		$(if $(filter true,$(SKIP_SCRIPTS)),--skip-scripts,) \
		$(if $(PR),--pr $(PR),)
	$(call ok,Postman collection generated)

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

# ==============================================================================
# User Management
# ==============================================================================
superuser: ## Create superuser
	$(MANAGE) createsuperuser

# ==============================================================================
# Static Files
# ==============================================================================
collectstatic: ## Collect static files
	$(MANAGE) collectstatic --noinput

