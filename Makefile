LUA ?= lua
PYTHON ?= scripts/python.sh
STYLUA ?= stylua
OUTPUT_DIR ?= dist

.PHONY: check validate check-lua package bump release fmt-lua lint-lua install

check: validate check-lua

validate:
	@$(PYTHON) scripts/widget.py validate

check-lua:
	@LUA="$(LUA)" scripts/check.sh

package:
	@$(PYTHON) scripts/widget.py package --output-dir "$(OUTPUT_DIR)"

bump:
	@test -n "$(LEVEL)" || (echo "LEVEL is required (patch, minor, or major)" >&2; exit 2)
	@$(PYTHON) scripts/widget.py bump --level "$(LEVEL)"
	@$(MAKE) check

release:
	@$(PYTHON) scripts/widget.py release
	@$(MAKE) check
	@$(PYTHON) scripts/widget.py release --publish

fmt-lua:
	@$(STYLUA) widget.lua tests

lint-lua:
	@$(STYLUA) --check widget.lua tests

install: check
	@easybar widgets install . --no-registry
	@echo "Reload EasyBar with: easybar config reload"
