SHELL				:= /bin/bash


lint: ## Run linter
	tox -e lint


requirements.txt: setup.py
	python3 -m venv _virtual_tmp
	. _virtual_tmp/bin/activate \
		&& pip install wheel \
		&& pip install . \
		&& pip freeze | grep -v license-manager > requirements.txt
	rm -rf _virtual_tmp


format: # reformat source python files
	isort license_manager setup.py
	black license_manager setup.py
