SHELL				:= /bin/bash
FUNCTION_REGION		:= us-west-2
FUNCTION_STAGE		:= edge


ifndef VIRTUAL_ENV
$(error VIRTUAL_ENV must be defined)
endif


requirements.txt: setup.py
	python3 -m venv _virtual_tmp
	. _virtual_tmp/bin/activate \
		&& pip install wheel \
		&& pip install . \
		&& pip freeze | grep -v license-manager > requirements.txt
	rm -rf _virtual_tmp


format: # reformat source python files
	isort src/licensemanager2 setup.py src/conftest.py
	black src/licensemanager2 setup.py src/conftest.py


function.zip:
	rm -rf $@ _lambda_tmp
	pip install -q --target _lambda_tmp wheel pip .
	cd _lambda_tmp && zip -q ../function.zip -r . -x '*.pyc'
	rm -rf _lambda_tmp
