# ==============================================================================
# Graphify — codebase knowledge graph for Cursor / agents
# Package: graphifyy (PyPI). CLI: graphify. Prefer: python -m graphify
# Docs: graphify-out/GRAPH_REPORT.md after first build
# ==============================================================================

# Override if needed: make graphify-update GRAPHIFY="uv run python -m graphify"
GRAPHIFY       ?= python -m graphify
GRAPHIFY_ROOT  ?= .
GRAPHIFY_EXCLUDE ?= "venv,.venv,*/migrations/*,*.pyc,node_modules,.git,htmlcov,.pytest_cache"

.PHONY: \
	graphify-pip \
	graphify-build \
	graphify-cluster \
	graphify-update \
	graphify-update-force \
	graphify-setup \
	graphify-cursor \
	graphify-cursor-uninstall \
	graphify-skill \
	graphify-query \
	graphify-path \
	graphify-explain \
	graphify-affected \
	graphify-watch \
	graphify-hook-install \
	graphify-hook-uninstall \
	graphify-hook-status \
	graphify-tree \
	graphify-check

graphify-pip: ## Install/upgrade graphifyy (PyPI; CLI command is graphify)
	$(call title,Installing graphifyy)
	python -m pip install --upgrade graphifyy
	$(call ok,graphifyy installed — use: make graphify-setup)

graphify-build: ## First/full code-only extract (no API key; AST only)
	$(call title,Graphify extract --code-only)
	$(GRAPHIFY) $(GRAPHIFY_ROOT) --code-only --exclude $(GRAPHIFY_EXCLUDE)
	$(call ok,graphify-out/graph.json written — next: make graphify-cluster)

graphify-cluster: ## Cluster graph + write GRAPH_REPORT.md (no HTML viz)
	$(call title,Graphify cluster-only)
	$(GRAPHIFY) cluster-only $(GRAPHIFY_ROOT) --no-viz --no-label
	$(call ok,GRAPH_REPORT.md updated)

graphify-update: ## Incremental re-extract after code changes (no API key)
	$(call title,Graphify update)
	$(GRAPHIFY) update $(GRAPHIFY_ROOT)
	$(call ok,Graph refreshed)

graphify-update-force: ## Force update after big deletes/refactors
	$(call title,Graphify update --force)
	$(GRAPHIFY) update $(GRAPHIFY_ROOT) --force
	$(call ok,Graph force-refreshed)

graphify-setup: graphify-build graphify-cluster graphify-cursor ## Full first-time setup (build + cluster + Cursor rule)
	$(call ok,Graphify ready — reload Cursor window (Developer: Reload Window))

graphify-cursor: ## Write .cursor/rules/graphify.mdc
	$(call title,Graphify cursor install)
	$(GRAPHIFY) cursor install
	$(call ok,.cursor/rules/graphify.mdc written)

graphify-cursor-uninstall: ## Remove Cursor graphify rule
	$(call title,Graphify cursor uninstall)
	$(GRAPHIFY) cursor uninstall
	$(call ok,Cursor graphify rule removed)

graphify-skill: ## Install global graphify skill (Claude / other agents)
	$(call title,Graphify install skill)
	$(GRAPHIFY) install
	$(call ok,Global skill installed)

graphify-query: ## Query graph (Q="how does billing expand charges?")
	@if [ -z "$(Q)" ]; then echo "Usage: make graphify-query Q=\"your question\""; exit 2; fi
	$(call title,Graphify query)
	$(GRAPHIFY) query "$(Q)"

graphify-path: ## Shortest path between symbols (A=Foo B=Bar)
	@if [ -z "$(A)" ] || [ -z "$(B)" ]; then echo "Usage: make graphify-path A=<from> B=<to>"; exit 2; fi
	$(call title,Graphify path $(A) -> $(B))
	$(GRAPHIFY) path "$(A)" "$(B)"

graphify-explain: ## Explain a node + neighbors (X=Patient)
	@if [ -z "$(X)" ]; then echo "Usage: make graphify-explain X=<symbol>"; exit 2; fi
	$(call title,Graphify explain $(X))
	$(GRAPHIFY) explain "$(X)"

graphify-affected: ## What breaks if X changes (X=Patient)
	@if [ -z "$(X)" ]; then echo "Usage: make graphify-affected X=<symbol>"; exit 2; fi
	$(call title,Graphify affected $(X))
	$(GRAPHIFY) affected "$(X)"

graphify-watch: ## Watch repo and rebuild graph on code changes
	$(call title,Graphify watch)
	$(GRAPHIFY) watch $(GRAPHIFY_ROOT)

graphify-hook-install: ## Install post-commit/checkout hooks to refresh graph
	$(call title,Graphify hook install)
	$(GRAPHIFY) hook install
	$(call ok,Graphify git hooks installed)

graphify-hook-uninstall: ## Remove graphify git hooks
	$(call title,Graphify hook uninstall)
	$(GRAPHIFY) hook uninstall
	$(call ok,Graphify git hooks removed)

graphify-hook-status: ## Show graphify git hook status
	$(GRAPHIFY) hook status

graphify-tree: ## Emit collapsible tree HTML (graphify-out/GRAPH_TREE.html)
	$(call title,Graphify tree)
	$(GRAPHIFY) tree
	$(call ok,graphify-out/GRAPH_TREE.html written)

graphify-check: ## Check if semantic re-extraction is pending
	$(GRAPHIFY) check-update $(GRAPHIFY_ROOT)
