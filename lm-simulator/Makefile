# TARGETS
install:
	poetry install

test: install
	poetry run pytest

lint: install
	poetry run flake8 lm_simulator tests --max-line-length=110
	poetry run isort --check lm_simulator tests
	poetry run black --check lm_simulator tests

format: install
	poetry run black lm_simulator tests
	poetry run isort lm_simulator tests

qa: test lint

local: install
	docker-compose up --build lm-simulator

setup:
	./scripts/create-dev-setup.sh $(lm_sim_ip)

clean: clean-eggs clean-build
	@find . -iname '*.pyc' -delete
	@find . -iname '*.pyo' -delete
	@find . -iname '*~' -delete
	@find . -iname '*.swp' -delete
	@find . -iname '__pycache__' -delete

clean-eggs:
	@find . -name '*.egg' -print0|xargs -0 rm -rf --
	@rm -rf .eggs/

clean-build:
	@rm -fr build/
	@rm -fr dist/
	@rm -fr *.egg-info

# SETTINGS
# Use one shell for all commands in a target recipe
.ONESHELL:
# Set default goal
.DEFAULT_GOAL := help
# Use bash shell in Make instead of sh 
SHELL := /bin/bash
