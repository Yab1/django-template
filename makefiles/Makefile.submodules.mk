# ==============================================================================
# Git Submodules
# ==============================================================================
.PHONY: submodule-init submodule-sync submodule-status submodule-update

submodule: ## Initialize or update submodules
	$(call title,Initializing or updating git submodules)
	@./scripts/submodule-init.sh
	$(call ok,Git submodules initialized or updated)

submodule-sync: ## Sync git submodules
	$(call title,Syncing git submodules)
	git submodule sync
	$(call ok,Git submodules synced)

submodule-status: ## Show git submodules status
	$(call title,Showing git submodules status)
	git submodule status
	$(call ok,Git submodules status shown)

submodule-update: ## Update git submodules
	$(call title,Updating git submodules)
	git submodule update --init --recursive
	$(call ok,Git submodules updated)

