.ONESHELL:
.DEFAULT_GOAL:=help
SHELL:=/bin/bash
PACKAGE_NAME:=lm_cli

.PHONY: install
install:
	uv sync --extra dev

.PHONY: test
test: install
	uv run pytest

.PHONY: mypy
mypy: install
	uv run mypy ${PACKAGE_NAME} --pretty

.PHONY: verify
verify: install
	uv run ruff check tests ${PACKAGE_NAME}
	uv run ruff format --check tests ${PACKAGE_NAME}

.PHONY: modify
modify: install
	uv run ruff check --fix tests ${PACKAGE_NAME}
	uv run ruff format tests ${PACKAGE_NAME}

.PHONY: qa
qa: test mypy verify
	echo "All quality checks pass!"

.PHONY: changes
changes:
	towncrier create --dir .. --section "CLI"

.PHONY: clean
clean:
	@find . -iname '*.pyc' -delete
	@find . -iname '*.pyo' -delete
	@find . -iname '*~' -delete
	@find . -iname '*.swp' -delete
	@find . -iname '__pycache__' -delete
	@rm -rf .mypy_cache
	@rm -rf .pytest_cache
	@find . -name '*.egg' -print0|xargs -0 rm -rf --
	@rm -rf .eggs/
	@rm -fr build/
	@rm -fr dist/
	@rm -fr *.egg-info

.PHONY: help
help: # Display target comments in 'make help'
	grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'
