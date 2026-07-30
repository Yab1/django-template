# ==============================================================================
# Git — deploy prep (rebase current branch onto latest main)
# ==============================================================================
# Default branch name is dev; override with BR=other-branch.
# ==============================================================================
BR ?= dev

.PHONY: rebase-main

rebase-main: ## Fetch origin/main and rebase onto it (BR=dev default; e.g. BR=feature/x). You push separately.
	@branch=$$(git rev-parse --abbrev-ref HEAD 2>/dev/null) || { echo "Not a git repository."; exit 1; }; \
	if [ "$$branch" != "$(BR)" ]; then \
	  echo "Refusing to run: current branch is '$$branch', expected '$(BR)' (set BR=... to match)."; \
	  exit 1; \
	fi
	$(call title,Fetching origin/main and rebasing $(BR))
	git fetch origin main
	git rebase origin/main
	$(call ok,$(BR) is rebased onto origin/main — push when ready: git push origin $(BR))
