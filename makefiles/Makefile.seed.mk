# ==============================================================================
# Database seeding (dev / local)
# Requires MANAGE, title, ok from the root Makefile.
# ==============================================================================
.PHONY: seed-superuser

seed-superuser: ## Load superusers from YAML secrets file (use UPDATE=1 to update existing)
	$(call title,Loading superusers from secrets file)
	$(MANAGE) load_superusers $(if $(UPDATE),--update,)
	$(call ok,Superusers loaded)
