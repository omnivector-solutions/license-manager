SHELL:=/bin/bash
ROOT_DIR:=$(shell dirname $(shell pwd))

install:
	poetry install

test: install
	poetry run pytest

mypy: install
	poetry run mypy lm_backend --pretty

lint: install
	poetry run flake8 lm_backend --max-line-length=110
	poetry run black --check lm_backend tests
	poetry run isort --check lm_backend tests

qa: test mypy lint
	echo "All tests pass! Ready for deployment"

format: install
	poetry run black lm_backend tests
	poetry run isort lm_backend tests

local:
	poetry run uvicorn --host 0.0.0.0 lm_backend.main:app --reload

clean: clean-eggs clean-build
	@find . -iname '*.pyc' -delete
	@find . -iname '*.pyo' -delete
	@find . -iname '*~' -delete
	@find . -iname '*.swp' -delete
	@find . -iname '__pycache__' -delete
	@rm -rf .tox

clean-eggs:
	@find . -name '*.egg' -print0|xargs -0 rm -rf --
	@rm -rf .eggs/

clean-build:
	@rm -fr build/
	@rm -fr dist/
	@rm -fr *.egg-info
