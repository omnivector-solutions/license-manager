# SETTINGS
# Use one shell for all commands in a target recipe
SHELL:=/bin/bash
.DEFAULT_GOAL:=help
ROOT_DIR:=$(shell dirname $(shell pwd))
PACKAGE_NAME:=lm_simulator

.PHONY: install
install:
	poetry install

.PHONY: verify
verify: install
	poetry run ruff check ${PACKAGE_NAME}
	poetry run ruff format --check ${PACKAGE_NAME}

.PHONY: modify
modify: install
	poetry run ruff check --fix ${PACKAGE_NAME}
	poetry run ruff format ${PACKAGE_NAME}

.PHONY: qa
qa: verify
	echo "All quality checks pass!"

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
