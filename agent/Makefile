install:
	poetry install

test: install
	poetry run pytest

mypy: install
	poetry run mypy lm_agent --pretty

lint: install
	poetry run flake8 lm_agent --max-line-length=110
	poetry run black --check lm_agent tests
	poetry run isort --check lm_agent tests

qa: test mypy lint
	echo "All tests pass! Ready for deployment"

format: install
	poetry run black lm_agent tests
	poetry run isort lm_agent tests

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

SHELL := /bin/bash
