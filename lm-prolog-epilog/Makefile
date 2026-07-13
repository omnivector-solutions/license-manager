# SETTINGS
# Use one shell for all commands in a target recipe
.ONESHELL:
.DEFAULT_GOAL:=help
SHELL:=/bin/bash

SCRIPTS:=$(wildcard *.sh)

.PHONY: install
install: ## Install test dependencies (bats + shellcheck)
	@if command -v bats >/dev/null 2>&1 && command -v shellcheck >/dev/null 2>&1; then \
		echo "bats and shellcheck already installed"; \
	elif command -v apt-get >/dev/null 2>&1; then \
		sudo apt-get update && sudo apt-get install -y bats shellcheck; \
	elif command -v brew >/dev/null 2>&1; then \
		brew install bats-core shellcheck; \
	else \
		echo "Please install 'bats' and 'shellcheck' manually" >&2; exit 1; \
	fi

.PHONY: test
test: install ## Run the bats test suite
	bats tests/

.PHONY: verify
verify: install ## Lint the shell scripts with shellcheck
	shellcheck -x $(SCRIPTS)

.PHONY: qa
qa: verify test ## Run all quality control checks
	echo "All quality checks pass!"

.PHONY: changes
changes: ## Create a changelog fragment
	towncrier create --dir .. --section "Prolog/Epilog"

.PHONY: clean
clean: ## Remove editor and temporary files
	@find . -iname '*~' -delete
	@find . -iname '*.swp' -delete

.PHONY: help
help: ## Display target comments in 'make help'
	grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'
