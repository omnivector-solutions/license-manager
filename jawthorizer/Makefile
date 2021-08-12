SHELL:=/bin/bash
ROOT_DIR:=$(shell dirname $(shell pwd))
LAMBDA_TARGET:=${ROOT_DIR}/function-jawthorizer.zip

install:
	poetry install

test: install
	poetry run pytest

lint: install
	poetry run black --check jawthorizer tests
	poetry run isort --check jawthorizer tests

qa: test lint
	echo "All tests pass! Ready for deployment"

format: install
	poetry run black jawthorizer tests
	poetry run isort jawthorizer tests

lambda:
	rm -f ${LAMBDA_TARGET}
	python3 -m venv _tmp_venv
	poetry config virtualenvs.create false --local
	source _tmp_venv/bin/activate && poetry install --no-dev
	cd _tmp_venv/lib/python*.*/site-packages && zip -qr9 ${LAMBDA_TARGET} .
	rm -rf _tmp_venv
	rm poetry.toml

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
