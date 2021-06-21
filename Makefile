SHELL				:= /bin/bash
FUNCTION_REGION		:= us-west-2
FUNCTION_STAGE		:= edge


format: # reformat source python files
	isort src/licensemanager2 src/conftest.py jawthorizer
	black src/licensemanager2 src/conftest.py jawthorizer


function.zip:
	rm -rf $@ _tmp_venv
	python3 -m virtualenv _tmp_venv
	. ./_tmp_venv/bin/activate \
            && pip install --upgrade wheel pip \
            && pip install .
	cd _tmp_venv/lib/python3.8/site-packages \
            && zip -9 -q ../../../../$@ -r . \
                && cd ../../../../
	rm -rf _tmp_venvi


function-jawthorizer.zip: jawthorizer/setup.py jawthorizer/src/jawthorizer/*.py
	rm -rf $@ _lambda_tmp _tmp_venv
	python3 -m virtualenv _tmp_venv
	. ./_tmp_venv/bin/activate \
            && pip install --upgrade wheel pip \
            && pip install -q --target _lambda_tmp ./jawthorizer
	cd _lambda_tmp && zip -q ../$@ -r .
	rm -rf _lambda_tmp _tmp_venv
