PY := python3

.PHONY: run test lint deps help

run: ## Run the CLI (loads .env for LLM_RATINGS_AA_API_KEY)
	set -a; . .env; set +a; $(PY) -m llmratings $(ARGS)

deps: ## Install Python dependencies (requirements.txt)
	# Homebrew Python is PEP 668 externally managed — no venv in this repo.
	$(PY) -m pip install --break-system-packages -r requirements.txt

test: ## Run the test suite
	$(PY) -m unittest discover -s tests

lint: ## Ruff if installed, else a syntax check
	@if command -v ruff >/dev/null 2>&1; then ruff check .; else $(PY) -m compileall -q llmratings; fi

help: ## Show this help
	@grep -E '^[a-z]+:.*##' $(MAKEFILE_LIST) | awk -F':.*## ' '{printf "%-8s %s\n", $$1, $$2}'
