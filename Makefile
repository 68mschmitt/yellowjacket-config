# Common local workflows for this ZMK config.
.DEFAULT_GOAL := help

DM_TEST_DIR ?= tests/dynamic_macro

WEST ?= west
BOARD ?= nice_nano@2.0.0//zmk
ZMK_APP ?= $(CURDIR)/../zmk/app
ZMK_CONFIG ?= $(CURDIR)/config
ZMK_EXTRA_MODULES ?= $(CURDIR)
WEST_BUILD_ROOT ?= $(CURDIR)/build
WEST_BUILD_ARGS ?=
CMAKE_ARGS ?=

YJ1_LEFT_SHIELD ?= yellowjacket_yj1_left
LOGGING_SHIELD ?= yellowjacket_yj1_left
LOGGING_SNIPPET ?= zmk-usb-logging

.PHONY: help test-dm clean-dm build-yj1-left build-logging

.PHONY: test-display preview-cats build-dongle
test-display: ## Render every cat layer using real LVGL (set LVGL_DIR).
	bash tests/pinchwing_display/run.sh

preview-cats: ## Open the playable desktop cat-layer demo.
	xdg-open "$(CURDIR)/previews/cat-layers/index.html"

build-dongle: ## Build all Pinchwing dongle targets (set ZMK_APP).
	ZMK_APP="$(ZMK_APP)" bash scripts/build-pinchwing-dongle.sh

help: ## Show available make targets and common override variables.
	@printf 'Targets:\n'
	@awk 'BEGIN {FS = ":.*##"} /^[a-zA-Z0-9_.-]+:.*##/ {printf "  %-18s %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@printf '\nCommon overrides:\n'
	@printf '  BOARD=%s\n' '$(BOARD)'
	@printf '  SHIELD=<target default; override per build target>\n'
	@printf '  ZMK_APP=%s\n' '$(ZMK_APP)'
	@printf '  ZMK_CONFIG=%s\n' '$(ZMK_CONFIG)'
	@printf '  ZMK_EXTRA_MODULES=%s\n' '$(ZMK_EXTRA_MODULES)'

test-dm: ## Build and run the dynamic macro host tests.
	$(MAKE) -C $(DM_TEST_DIR) test

clean-dm: ## Remove generated dynamic macro host test artifacts.
	$(MAKE) -C $(DM_TEST_DIR) clean

build-yj1-left: SHIELD ?= $(YJ1_LEFT_SHIELD)
build-yj1-left: WEST_BUILD_DIR ?= $(WEST_BUILD_ROOT)/yj1-left
build-yj1-left: ## Build YJ1 left firmware with west (override BOARD/SHIELD/ZMK_* as needed).
	$(WEST) build -s "$(ZMK_APP)" -d "$(WEST_BUILD_DIR)" -b "$(BOARD)" $(WEST_BUILD_ARGS) -- -DSHIELD="$(SHIELD)" -DZMK_CONFIG="$(ZMK_CONFIG)" -DZMK_EXTRA_MODULES="$(ZMK_EXTRA_MODULES)" $(CMAKE_ARGS)

build-logging: SHIELD ?= $(LOGGING_SHIELD)
build-logging: WEST_BUILD_DIR ?= $(WEST_BUILD_ROOT)/yj1-left-logging
build-logging: ## Build YJ1 left firmware with the ZMK USB logging snippet.
	$(WEST) build -s "$(ZMK_APP)" -d "$(WEST_BUILD_DIR)" -b "$(BOARD)" -S "$(LOGGING_SNIPPET)" $(WEST_BUILD_ARGS) -- -DSHIELD="$(SHIELD)" -DZMK_CONFIG="$(ZMK_CONFIG)" -DZMK_EXTRA_MODULES="$(ZMK_EXTRA_MODULES)" $(CMAKE_ARGS)
