# Copyright (c) 2024 The ZMK Contributors
# SPDX-License-Identifier: MIT
#
# This zmk-config doubles as a Zephyr/ZMK module (see zephyr/module.yml) so it
# can carry out-of-tree behaviors alongside its shields.

# Absolute paths: the `app` target is created in ZMK's directory, not ours.
target_include_directories(app PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/include)

# Recording and playback both operate on resolved keycode events, which on a
# split keyboard only exist on the central half. This guard is required, not an
# optimisation: upstream compiles src/events/keycode_state_changed.c on the
# central only, so raise_zmk_keycode_state_changed() does not exist elsewhere.
if((NOT CONFIG_ZMK_SPLIT) OR CONFIG_ZMK_SPLIT_ROLE_CENTRAL)
  target_sources_ifdef(CONFIG_ZMK_BEHAVIOR_DYNAMIC_MACRO app PRIVATE
                       ${CMAKE_CURRENT_SOURCE_DIR}/src/behaviors/behavior_dynamic_macro.c)
endif()
