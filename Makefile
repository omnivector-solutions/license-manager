SHELL				:= /bin/bash
FUNCTION_REGION		:= us-west-2
FUNCTION_STAGE		:= edge

-include .env

TERRAFORM_LIVE_PATH	:= ../infrastructure/live/$(FUNCTION_STAGE)/license-manager
export AWS_REGION	:= $(FUNCTION_REGION)


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
	isort src/licensemanager2 setup.py conftest.py
	black src/licensemanager2 setup.py conftest.py


function.zip:
	rm -f $@
	pip install -q --target _lambda_tmp .
	cd _lambda_tmp && zip -q ../function.zip -r . -x '*.pyc'
	rm -rf _lambda_tmp


terraform-apply: function.zip
	export TF_VAR_zipfile="$(shell realpath $^)"; \
	cd $(TERRAFORM_LIVE_PATH); \
	terraform taint module.license-manager-lambda.aws_lambda_function.license-manager; \
	terraform plan; \
	terraform apply -auto-approve -lock=true


terraform-show:
	cd $(TERRAFORM_LIVE_PATH); terraform show


terraform-destroy-for-reference-only:
	export TF_VAR_zipfile="__ignored"; \
	cd $(TERRAFORM_LIVE_PATH); terraform destroy -lock=true


$(TERRAFORM_LIVE_PATH)/backend.tf: deployment/backend.tf.in
	envsubst < $^ > $@


backend.tf: $(TERRAFORM_LIVE_PATH)/backend.tf
