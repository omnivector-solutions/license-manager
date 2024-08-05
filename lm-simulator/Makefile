# SETTINGS
# Use one shell for all commands in a target recipe
SHELL:=/bin/bash
.DEFAULT_GOAL:=help
ROOT_DIR:=$(shell dirname $(shell pwd))
PACKAGE_NAME:=lm_simulator

.PHONY: install
install:
	poetry install

.PHONY: test
test:
	docker compose up --build unittest
	docker compose run --rm unittest

.PHONY: lint
lint: install
	poetry run flake8 lm_simulator tests --max-line-length=110
	poetry run isort --check lm_simulator tests
	poetry run black --check lm_simulator tests

.PHONY: format
format: install
	poetry run black lm_simulator tests
	poetry run isort lm_simulator tests

.PHONY: qa
qa: test lint
	echo "All quality checks pass!"

.PHONY: local
local: install
	docker compose up --build lm-simulator

.PHONY: setup
setup:
	./scripts/create-dev-setup.sh $(lm_sim_ip)

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
