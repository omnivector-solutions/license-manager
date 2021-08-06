SHELL:= /bin/bash

qa:
	$(MAKE) -C backend qa
	$(MAKE) -C agent qa
	$(MAKE) -C jawthorizer qa

format:
	$(MAKE) -C backend format
	$(MAKE) -C agent format
	$(MAKE) -C jawthorizer format

clean:
	$(MAKE) -C backend clean
	$(MAKE) -C agent clean
	$(MAKE) -C jawthorizer clean

lambda:
	$(MAKE) -C backend lambda
	$(MAKE) -C jawthorizer lambda
