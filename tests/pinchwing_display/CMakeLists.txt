cmake_minimum_required(VERSION 3.20)
project(pinchwing_display_test C)
if(NOT LVGL_DIR)
  message(FATAL_ERROR "Set LVGL_DIR to the LVGL checkout used by the firmware")
endif()
unset(LV_CONF_PATH CACHE)
include_directories("${CMAKE_CURRENT_SOURCE_DIR}")
add_compile_definitions(LV_CONF_INCLUDE_SIMPLE)
set(LV_CONF_BUILD_DISABLE_EXAMPLES ON CACHE BOOL "" FORCE)
set(LV_CONF_BUILD_DISABLE_DEMOS ON CACHE BOOL "" FORCE)
add_subdirectory("${LVGL_DIR}" lvgl)
add_executable(display_test main.c
  ../../src/display/pinchwing_pet.c
  ../../src/display/pinchwing_scenes.c
  ../../src/display/cat_overlays.c
  ../../src/display/bongo_cat.c)
target_include_directories(display_test PRIVATE stubs ../../src/display)
target_link_libraries(display_test PRIVATE lvgl m)
target_compile_options(display_test PRIVATE -Wall -Wextra -Werror)
