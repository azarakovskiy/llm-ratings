PY := python3

.PHONY: run test lint help

run: ## Serve the local web app (loads .env; forwards ARGS)
	set -a; . .env; set +a; $(PY) -m llmratings --web $(ARGS)

test: ## Run the test suite
	$(PY) -m unittest discover -s tests

lint: ## Ruff if installed, else a syntax check
	@if command -v ruff >/dev/null 2>&1; then ruff check .; else $(PY) -m compileall -q llmratings; fi

help: ## Show this help
	@grep -E '^[a-z]+:.*##' $(MAKEFILE_LIST) | awk -F':.*## ' '{printf "%-8s %s\n", $$1, $$2}'
