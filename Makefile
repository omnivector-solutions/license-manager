SHELL:= /bin/bash

install:
	$(MAKE) -C backend install
	$(MAKE) -C agent install
	$(MAKE) -C lm-cli install

qa:
	$(MAKE) -C backend qa
	$(MAKE) -C agent qa
	$(MAKE) -C lm-cli qa

format:
	$(MAKE) -C backend format
	$(MAKE) -C agent format
	$(MAKE) -C lm-cli format

clean:
	$(MAKE) -C backend clean
	$(MAKE) -C agent clean
	$(MAKE) -C lm-cli clean
