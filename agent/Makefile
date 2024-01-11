# SETTINGS
# Use one shell for all commands in a target recipe
.ONESHELL:
.DEFAULT_GOAL:=help
SHELL:=/bin/bash
PACKAGE_NAME:=lm_agent

.PHONY: install
install:
	poetry install

.PHONY: test
test: install
	poetry run pytest

.PHONY: mypy
mypy: install
	poetry run mypy ${PACKAGE_NAME} --pretty

.PHONY: lint
lint: install
	poetry run ruff check ${PACKAGE_NAME}
	poetry run ruff check tests

.PHONY: qa
qa: test mypy lint
	echo "All quality checks pass!"

.PHONY: format
format: install
	poetry run ruff format ${PACKAGE_NAME}
	poetry run ruff format tests

.PHONY: release-%
release-%:
	../release-scripts/prepare-release.sh $(subst release-,,$@)

.PHONY: publish
publish:
	../release-scripts/publish-release.sh

.PHONY: clean
clean:
	@find . -iname '*.pyc' -delete
	@find . -iname '*.pyo' -delete
	@find . -iname '*~' -delete
	@find . -iname '*.swp' -delete
	@find . -iname '__pycache__' -delete
	@rm -rf .tox
	@find . -name '*.egg' -print0|xargs -0 rm -rf --
	@rm -rf .eggs/
	@rm -fr build/
	@rm -fr dist/
	@rm -fr *.egg-info

.PHONY: help
help: # Display target comments in 'make help'
	grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'
