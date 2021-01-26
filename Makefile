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
	isort src/licensemanager2 setup.py
	black src/licensemanager2 setup.py


#FUNCTION_NAME       = serverless-fastapi
#
#ifndef VIRTUAL_ENV
#$(error VIRTUAL_ENV must be defined)
#endif
#
#function.zip:
#	rm -f $@
#	python3 -m venv _virtual_tmp
#	. _virtual_tmp/bin/activate \
#		&& pip install uvicorn mangum fastapi
#	cd _virtual_tmp/lib/python*/site-packages && zip ../../../../function.zip -r . -x '*.pyc'
#	zip -g ./function.zip -r app -x '*.pyc'
#	rm -rf _virtual_tmp
#
#update-function: function.zip
#	aws --region $(FUNCTION_REGION) \
#		lambda update-function-code \
#		--function-name $(FUNCTION_NAME) \
#		--zip-file fileb://$^
#	aws --region $(FUNCTION_REGION) \
#		lambda update-function-configuration \
#		--function-name $(FUNCTION_NAME) \
#		--environment "Variables={ASGI_ROOT_PATH=/asdf}"
#
#
