# Host-side test for src/behaviors/behavior_dynamic_macro.c.
# Compiles the real driver against stub Zephyr/ZMK headers; no SDK needed.
#   make && ./test
CFLAGS = -std=gnu11 -I. -Wall -Wextra -Wno-unused-parameter -Wno-unused-function -g

test: test.c stubs.h ../../src/behaviors/behavior_dynamic_macro.c
	@mkdir -p dt-bindings/zmk zephyr/logging drivers zmk/events
	@cp ../../include/dt-bindings/zmk/dynamic_macro.h dt-bindings/zmk/
	@cp ../../src/behaviors/behavior_dynamic_macro.c .
	@for f in zephyr/device.h zephyr/kernel.h zephyr/logging/log.h \
	          drivers/behavior.h zmk/behavior.h zmk/event_manager.h \
	          zmk/events/keycode_state_changed.h; do \
	    echo '#include "stubs.h"' > $$f; \
	done
	$(CC) $(CFLAGS) -o test test.c

clean:
	rm -rf test test.dSYM dt-bindings zephyr drivers zmk behavior_dynamic_macro.c

.PHONY: clean
