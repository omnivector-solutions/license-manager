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
	isort src/licensemanager2 setup.py src/conftest.py authorizer
	black src/licensemanager2 setup.py src/conftest.py authorizer


PIP_INSTALL_FOR_ZIP		:= pip install -q --target _lambda_tmp wheel pip


function.zip:
	rm -rf $@ _lambda_tmp
	$(PIP_INSTALL_FOR_ZIP) .

	# anecdotally, not including pyc files slows down lambda execution,
	# so we don't remove them
	cd _lambda_tmp && zip -9 -q ../$@ -r .
	rm -rf _lambda_tmp


function-authorizer.zip: authorizer/setup.py authorizer/authorizer.py
	rm -rf $@ _lambda_tmp
	$(PIP_INSTALL_FOR_ZIP) ./authorizer

	cd _lambda_tmp && zip -q ../$@ -r .
	rm -rf _lambda_tmp
