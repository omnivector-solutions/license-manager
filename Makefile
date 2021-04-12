SHELL				:= /bin/bash
FUNCTION_REGION		:= us-west-2
FUNCTION_STAGE		:= edge


ifndef VIRTUAL_ENV
$(error VIRTUAL_ENV must be defined)
endif


requirements.txt: pyproject.toml
	python3 -m venv _virtual_tmp
	. _virtual_tmp/bin/activate \
		&& pip install wheel \
		&& pip install . \
		&& pip freeze | grep -v license-manager > requirements.txt
	rm -rf _virtual_tmp


format: # reformat source python files
	isort src/licensemanager2 src/conftest.py jawthorizer
	black src/licensemanager2 src/conftest.py jawthorizer


PIP_INSTALL_FOR_ZIP		:= pip install -q --target _lambda_tmp wheel pip


function.zip:
	rm -rf $@ _lambda_tmp
	$(PIP_INSTALL_FOR_ZIP) .

	# anecdotally, not including pyc files slows down lambda execution,
	# so we don't remove them
	cd _lambda_tmp && zip -9 -q ../$@ -r .
	rm -rf _lambda_tmp


function-jawthorizer.zip: jawthorizer/setup.py jawthorizer/src/jawthorizer/*.py
	rm -rf $@ _lambda_tmp
	$(PIP_INSTALL_FOR_ZIP) ./jawthorizer

	cd _lambda_tmp && zip -q ../$@ -r .
	rm -rf _lambda_tmp
