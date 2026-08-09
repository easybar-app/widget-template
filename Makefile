LUA ?= lua
PYTHON ?= scripts/python.sh
STYLUA ?= stylua
PRETTIER ?= npx --yes prettier@3.9.6
TAPLO ?= npx --yes @taplo/cli@0.7.0
OUTPUT_DIR ?= dist
PRETTIER_MD_SOURCES := README.md AGENTS.md
PRETTIER_YAML_SOURCES := ".github/**/*.{yml,yaml}"
PRETTIER_JSON_SOURCES := ".github/**/*.json" .luarc.json
TAPLO_SOURCES := .stylua.toml package.toml

.DEFAULT_GOAL := help

.PHONY: help fmt fmt-lua fmt-md fmt-yaml fmt-json fmt-toml lint-lua check validate check-lua package bump release install

help: ## Display this help.
	@awk 'BEGIN {FS = ":.*##"; printf "\nUsage:\n  make \033[36m<target>\033[0m\n"} /^[a-zA-Z\_0-9-]+:.*?##/ { printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2 } /^##@/ { printf "\n\033[1m%s\033[0m\n", substr($$0, 5) }' $(MAKEFILE_LIST)

##@ Formatting

fmt: fmt-lua fmt-md fmt-yaml fmt-json fmt-toml ## Format all supported source and configuration files.

fmt-lua: ## Format Lua source and tests with StyLua.
	@$(STYLUA) widget.lua tests

fmt-md: ## Format Markdown files with Prettier.
	@$(PRETTIER) --write $(PRETTIER_MD_SOURCES)

fmt-yaml: ## Format YAML files with Prettier.
	@$(PRETTIER) --write $(PRETTIER_YAML_SOURCES)

fmt-json: ## Format JSON configuration files with Prettier.
	@$(PRETTIER) --write $(PRETTIER_JSON_SOURCES)

fmt-toml: ## Format TOML files with Taplo.
	@$(TAPLO) fmt $(TAPLO_SOURCES)

lint-lua: ## Check Lua formatting with StyLua.
	@$(STYLUA) --check widget.lua tests

##@ Validation

check: validate check-lua ## Validate the manifest and run Lua checks.

validate: ## Validate the widget manifest.
	@$(PYTHON) scripts/widget.py validate

check-lua: ## Check Lua syntax and run widget tests.
	@LUA="$(LUA)" scripts/check.sh

##@ Packaging

package: ## Build the widget release archive.
	@$(PYTHON) scripts/widget.py package --output-dir "$(OUTPUT_DIR)"

bump: ## Bump the package version with LEVEL=patch|minor|major.
	@test -n "$(LEVEL)" || (echo "LEVEL is required (patch, minor, or major)" >&2; exit 2)
	@$(PYTHON) scripts/widget.py bump --level "$(LEVEL)"
	@$(MAKE) check

release: ## Validate and publish the current package version.
	@$(PYTHON) scripts/widget.py release
	@$(MAKE) check
	@$(PYTHON) scripts/widget.py release --publish

##@ Development

install: check ## Install the widget from this checkout.
	@easybar widgets install . --no-registry
	@echo "Reload EasyBar with: easybar config reload"
