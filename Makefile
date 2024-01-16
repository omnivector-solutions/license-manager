SHELL:= /bin/bash

install:
	$(MAKE) -C agent install
	$(MAKE) -C lm-api install
	$(MAKE) -C lm-cli install

test:
	$(MAKE) -C agent test
	$(MAKE) -C lm-api test
	$(MAKE) -C lm-cli test

qa:
	$(MAKE) -C agent qa
	$(MAKE) -C lm-api qa
	$(MAKE) -C lm-cli qa

format:
	$(MAKE) -C agent format
	$(MAKE) -C lm-api format
	$(MAKE) -C lm-cli format

clean:
	$(MAKE) -C agent clean
	$(MAKE) -C lm-api clean
	$(MAKE) -C lm-cli clean
