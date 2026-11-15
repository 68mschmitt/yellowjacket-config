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

if(CONFIG_SHIELD_PINCHWING_SHARP OR CONFIG_SHIELD_PINCHWING_ROUND)
  target_sources(app PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/src/display/pinchwing_status.c)
endif()

target_sources_ifdef(CONFIG_SHIELD_PINCHWING_ROUND app PRIVATE
                      ${CMAKE_CURRENT_SOURCE_DIR}/src/display/pinchwing_pet.c
                      ${CMAKE_CURRENT_SOURCE_DIR}/src/display/pinchwing_scenes.c
                      ${CMAKE_CURRENT_SOURCE_DIR}/src/display/cat_overlays.c
                      ${CMAKE_CURRENT_SOURCE_DIR}/src/display/bongo_cat.c)

if(CONFIG_SHIELD_PINCHWING_DONGLE_RIGHT OR CONFIG_SHIELD_PINCHWING_DONGLE_RECEIVER)
  target_sources(app PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/src/pointing/pinchwing_dpi.c)
endif()

if(CONFIG_SHIELD_PINCHWING_DONGLE_LEFT OR CONFIG_SHIELD_PINCHWING_DONGLE_RIGHT OR
   CONFIG_SHIELD_PINCHWING_DONGLE_RECEIVER)
  target_sources(app PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/src/pinchwing_power.c)
endif()

if(CONFIG_SHIELD_YELLOWJACKET_MOUSE_LEFT OR CONFIG_SHIELD_YELLOWJACKET_MOUSE_RIGHT OR
   CONFIG_SHIELD_PINCHWING_DONGLE_LEFT OR CONFIG_SHIELD_PINCHWING_DONGLE_RIGHT OR
   CONFIG_SHIELD_PINCHWING_DONGLE_RECEIVER)
  target_include_directories(app PRIVATE ${ZEPHYR_ZMK_PMW3610_DRIVER_MODULE_DIR}/src)
  target_sources(app PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/src/behaviors/behavior_pmw3610_dpi.c)
endif()
