# Host-side test for src/behaviors/behavior_dynamic_macro.c.
# Compiles the real driver against stub Zephyr/ZMK headers; no SDK needed.
#   make

BUILD_DIR ?= build

CPPFLAGS += -I$(BUILD_DIR) -I$(CURDIR)
CFLAGS ?= -std=gnu11 -Wall -Wextra -Wno-unused-parameter -Wno-unused-function -g

DRIVER_SRC := ../../src/behaviors/behavior_dynamic_macro.c
DRIVER_COPY := $(BUILD_DIR)/behavior_dynamic_macro.c
BINDING_SRC := ../../include/dt-bindings/zmk/dynamic_macro.h
BINDING_COPY := $(BUILD_DIR)/dt-bindings/zmk/dynamic_macro.h
STUB_HEADERS := \
	$(BUILD_DIR)/zephyr/device.h \
	$(BUILD_DIR)/zephyr/kernel.h \
	$(BUILD_DIR)/zephyr/logging/log.h \
	$(BUILD_DIR)/drivers/behavior.h \
	$(BUILD_DIR)/zmk/behavior.h \
	$(BUILD_DIR)/zmk/event_manager.h \
	$(BUILD_DIR)/zmk/events/keycode_state_changed.h
TEST_BIN := $(BUILD_DIR)/test

.PHONY: test clean

test: $(TEST_BIN)
	$(TEST_BIN)

$(TEST_BIN): test.c stubs.h $(DRIVER_COPY) $(BINDING_COPY) $(STUB_HEADERS)
	@mkdir -p $(@D)
	$(CC) $(CPPFLAGS) $(CFLAGS) -o $@ test.c

$(DRIVER_COPY): $(DRIVER_SRC)
	@mkdir -p $(@D)
	@cp $< $@

$(BINDING_COPY): $(BINDING_SRC)
	@mkdir -p $(@D)
	@cp $< $@

$(STUB_HEADERS):
	@mkdir -p $(@D)
	@printf '%s\n' '#include "stubs.h"' > $@

clean:
	rm -rf $(BUILD_DIR)
