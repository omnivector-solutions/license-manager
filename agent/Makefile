install:
	poetry install

test: install
	poetry run pytest

mypy: install
	poetry run mypy app --pretty

lint: install
	poetry run black --check app tests
	poetry run isort --check app tests

qa: test mypy lint
	echo "All tests pass! Ready for deployment"

format: install
	poetry run black app tests
	poetry run isort app tests

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
