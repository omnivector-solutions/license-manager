# SETTINGS
# Use one shell for all commands in a target recipe
SHELL:=/bin/bash
.DEFAULT_GOAL:=help
ROOT_DIR:=$(shell dirname $(shell pwd))
PACKAGE_NAME:=lm_simulator_api

.PHONY: install
install:
	poetry install

.PHONY: test
test:
	docker compose up --build unittest
	docker compose run --rm unittest

.PHONY: lint
lint: install
	poetry run ruff check --fix --select I ${PACKAGE_NAME} tests

.PHONY: format
format: install lint
	poetry run ruff format ${PACKAGE_NAME} tests

.PHONY: qa
qa: test lint
	echo "All quality checks pass!"

.PHONY: local
local: install
	docker compose up --build lm-simulator

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
