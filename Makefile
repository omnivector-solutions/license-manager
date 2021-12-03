SHELL:= /bin/bash

install:
	$(MAKE) -C backend install
	$(MAKE) -C agent install

qa:
	$(MAKE) -C backend qa
	$(MAKE) -C agent qa

format:
	$(MAKE) -C backend format
	$(MAKE) -C agent format

clean:
	$(MAKE) -C backend clean
	$(MAKE) -C agent clean
