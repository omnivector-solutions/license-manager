# SETTINGS
# Use one shell for all commands in a target recipe
SHELL:=/bin/bash
.DEFAULT_GOAL:=help
ROOT_DIR:=$(shell dirname $(shell pwd))
PACKAGE_NAME:=lm_simulator

.PHONY: install
install:
	uv sync --extra dev

.PHONY: verify
verify: install
	uv run ruff check ${PACKAGE_NAME}
	uv run ruff format --check ${PACKAGE_NAME}

.PHONY: modify
modify: install
	uv run ruff check --fix ${PACKAGE_NAME}
	uv run ruff format ${PACKAGE_NAME}

.PHONY: qa
qa: verify
	echo "All quality checks pass!"

.PHONY: changes
changes:
	towncrier create --dir .. --section "Simulator"

.PHONY: clean
clean: clean-eggs clean-build
	@find . -iname '*.pyc' -delete
	@find . -iname '*.pyo' -delete
	@find . -iname '*~' -delete
	@find . -iname '*.swp' -delete
	@find . -iname '__pycache__' -delete
	@find . -name '*.egg' -print0|xargs -0 rm -rf --
	@rm -rf .eggs/
	@rm -fr build/
	@rm -fr dist/
	@rm -fr *.egg-info
