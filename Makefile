SHELL:= /bin/bash

install:
	$(MAKE) -C lm-agent install
	$(MAKE) -C lm-api install
	$(MAKE) -C lm-cli install
	$(MAKE) -C lm-simulator install
	$(MAKE) -C lm-simulator-api install

test:
	$(MAKE) -C lm-agent test
	$(MAKE) -C lm-api test
	$(MAKE) -C lm-cli test
	$(MAKE) -C lm-simulator-api test

qa:
	$(MAKE) -C lm-agent qa
	$(MAKE) -C lm-api qa
	$(MAKE) -C lm-cli qa
	$(MAKE) -C lm-simulator qa
	$(MAKE) -C lm-simulator-api qa
	$(MAKE) -C lm-agent-snap qa

verify:
	$(MAKE) -C lm-agent verify
	$(MAKE) -C lm-api verify
	$(MAKE) -C lm-cli verify
	$(MAKE) -C lm-simulator verify
	$(MAKE) -C lm-simulator-api verify
	$(MAKE) -C lm-agent-snap verify

modify:
	$(MAKE) -C lm-agent modify
	$(MAKE) -C lm-api modify
	$(MAKE) -C lm-cli modify
	$(MAKE) -C lm-simulator modify
	$(MAKE) -C lm-simulator-api modify
	$(MAKE) -C lm-agent-snap modify

clean:
	$(MAKE) -C lm-agent clean
	$(MAKE) -C lm-api clean
	$(MAKE) -C lm-cli clean
	$(MAKE) -C lm-simulator clean
	$(MAKE) -C lm-simulator-api clean
	$(MAKE) -C lm-agent-snap clean

.PHONY: changes
changes:
	towncrier create --dir .

.PHONY: changelog-draft
changelog-draft:
	towncrier build --draft --version $$(uv version --short --directory lm-agent)

.PHONY: changelog-build
changelog-build:
	towncrier build --yes --version $$(uv version --short --directory lm-agent)
