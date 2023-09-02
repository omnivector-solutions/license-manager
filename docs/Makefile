# SETTINGS
# Use one shell for all commands in a target recipe
SHELL:=/bin/bash
.DEFAULT_GOAL:=help
ROOT_DIR:=$(shell dirname $(shell pwd))
PACKAGE_NAME:=src

.PHONY: install
install:
	poetry install

.PHONY: docs
docs: install
	poetry run mkdocs build

.PHONY: clean
clean:
	@find . -iname '*.pyc' -delete
	@find . -iname '*.pyo' -delete
	@find . -iname '*~' -delete
	@find . -iname '*.swp' -delete
	@find . -iname '__pycache__' -delete
	@rm -fr build/
	@rm -fr dist/
	@rm -fr *.egg-info

.PHONY: help
help: # Display target comments in 'make help'
	grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'
