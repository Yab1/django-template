# ==============================================================================
# Database seeding & fixtures (dev / local)
# Requires MANAGE, title, ok from the root Makefile.
# ==============================================================================
.PHONY: seed-fixtures seed-fixtures-reset seed-fixture seed-terminology seed-superuser seed-patients seed-practitioners seed-practitioner-roles seed-organization-chart seed-patient-chart seed-medication-fulfillment-catalog load-fixtures-ordered

# Ordered fixture load (terminology → resources → policies → bundles → assignments).
# Uses loaddata_replace — safe to re-run on non-empty DB. See scripts/load_fixtures.sh.
load-fixtures-ordered: ## Load fixtures in dependency order: ./scripts/load_fixtures.sh (optional PROFILE=security)
	$(call title,Loading fixtures (ordered))
	@MANAGE='$(MANAGE)' ./scripts/load_fixtures.sh --profile $(or $(PROFILE),full)
	$(call ok,Ordered fixtures loaded)

# -----------------------------------------------------------------------------
# Fixtures (override FIXTURES or use seed-fixture FIXTURE=name)
# -----------------------------------------------------------------------------
TERMINOLOGY_FIXTURES ?= publication_status

# All JSON under core/*/fixtures/ (sorted). loaddata uses raw INSERT—re-run fails on unique keys
# (e.g. resource_definition_resource.code) unless the DB is empty. Use seed-fixtures-reset for a clean load.
seed-fixtures: ## Load all JSON fixtures (sorted). Empty DB only; re-run use seed-fixtures-reset
	$(call title,Loading fixtures)
	@rd_res=$$(find "$$(pwd)/core/resource_definition/fixtures/resources" -type f -name '*.json' 2>/dev/null | sort); \
	if [ -n "$$rd_res" ]; then $(MANAGE) loaddata $$rd_res; fi
	@$(MANAGE) loaddata $$(find core -type f -name '*.json' -path '*/fixtures/*' ! -path '*/resource_definition/fixtures/resources/*' | sort)
	$(call ok,Fixtures loaded)

# Destructive: drops all tables in the default DB, then loads fixtures. Local dev only.
seed-fixtures-reset: ## flush --no-input then seed-fixtures (full wipe + reload)
	$(call title,Flushing database (all data))
	$(MANAGE) flush --no-input
	@$(MAKE) seed-fixtures

seed-fixture: ## Load one fixture: make seed-fixture FIXTURE=publication_status
	@$(if $(FIXTURE),,$(error FIXTURE= is required. Example: make seed-fixture FIXTURE=publication_status))
	$(call title,Loading fixture $(FIXTURE))
	$(MANAGE) loaddata $(FIXTURE)
	$(call ok,Fixture $(FIXTURE) loaded)

seed-terminology: ## Load terminology fixtures (uses TERMINOLOGY_FIXTURES)
	$(call title,Loading terminology fixtures)
	$(MANAGE) loaddata $(TERMINOLOGY_FIXTURES)
	$(call ok,Terminology seeded)

# -----------------------------------------------------------------------------
# Users & demo data
# -----------------------------------------------------------------------------
seed-superuser: ## Load superusers from YAML secrets file (use --update to update existing)
	$(call title,Loading superusers from secrets file)
	$(MANAGE) load_superusers $(if $(UPDATE),--update,)

seed-patients: ## Seed N new demo patients (optional NUMBER=5; default 1). Run seed-fixtures first.
	$(call title,Seeding demo patients)
	$(MANAGE) seed_patients $(if $(NUMBER),--number $(NUMBER),)
	$(call ok,Demo patients seeded)

seed-practitioners: ## Seed N new demo practitioners (optional NUMBER=5; default 1). Run seed-fixtures first.
	$(call title,Seeding demo practitioners)
	$(MANAGE) seed_practitioners $(if $(NUMBER),--number $(NUMBER),)
	$(call ok,Demo practitioners seeded)

seed-practitioner-roles: ## One-time: PractitionerRole for practitioners missing roles (optional ORG LOC AS_USER; DRY=1 dry-run; NO_LOC=1 skip location)
	$(call title,Seeding practitioner roles for existing practitioners)
	$(MANAGE) seed_practitioner_roles $(if $(ORG),--organization-id $(ORG),) $(if $(LOC),--location-id $(LOC),) $(if $(NO_LOC),--no-location,) $(if $(AS_USER),--requesting-user-id $(AS_USER),) $(if $(DRY),--dry-run,)
	$(call ok,Practitioner roles seed step finished)

seed-organization-chart: ## revenue_primary + cash_till per org (ETB/USD/EUR). Optional ORG=uuid CURRENCY=ETB DRY=1
	$(call title,Seeding organization chart accounts)
	$(MANAGE) seed_organization_chart $(if $(ORG),--organization-id $(ORG),) $(if $(CURRENCY),--currency-code $(CURRENCY),) $(if $(DRY),--dry-run,)
	$(call ok,Organization chart accounts seeded)

seed-patient-chart: ## Patient AR per patient×org×currency. Optional PATIENT=uuid ORG=uuid CURRENCY=ETB DRY=1
	$(call title,Seeding patient receivable accounts)
	$(MANAGE) seed_patient_chart $(if $(PATIENT),--patient-id $(PATIENT),) $(if $(ORG),--organization-id $(ORG),) $(if $(CURRENCY),--currency-code $(CURRENCY),) $(if $(DRY),--dry-run,)
	$(call ok,Patient receivable accounts seeded)

seed-medication-fulfillment-catalog: ## Full med fulfillment seed. Source: ALL=1 | CODE=uuid | VALUESET=url. Tenants: TENANT=opd|ed|peds or ALL_TENANTS=1. Optional ENSURE_PKG=1 ENSURE_PRICE=1 SKIP_STOCK=1 LIMIT QTY PRICE ORG LOC PKG AS_USER DRY=1 EXTRA=
	$(call title,Seeding medication fulfillment catalog)
	$(MANAGE) seed_medication_fulfillment_catalog \
		$(if $(ALL),--all,) \
		$(if $(CODE),--medication-code-id $(CODE),) \
		$(if $(VALUESET),--valueset-url $(VALUESET),) \
		$(if $(TENANT),--tenant $(TENANT),) \
		$(if $(ALL_TENANTS),--all-tenants,) \
		$(if $(ORG),--organization-id $(ORG),) \
		$(if $(LOC),--location-id $(LOC),) \
		$(if $(PKG),--package-code $(PKG),) \
		$(if $(ENSURE_PKG),--ensure-package,) \
		$(if $(ENSURE_PRICE),--ensure-pricing-config,) \
		$(if $(SKIP_STOCK),--skip-stock,) \
		$(if $(LIMIT),--limit $(LIMIT),) \
		$(if $(QTY),--opening-qty $(QTY),) \
		$(if $(PRICE),--unit-price $(PRICE),) \
		$(if $(AS_USER),--requesting-user-id $(AS_USER),) \
		$(if $(DRY),--dry-run,) \
		$(EXTRA)
	$(call ok,Medication fulfillment catalog seed finished)
