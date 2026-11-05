# prospi3 - ReXGlue Recompiled Project
#
# SDK boilerplate lives in generated/rexglue.cmake.

cmake_minimum_required(VERSION 3.25)
project(prospi3 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 23)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

include(generated/rexglue.cmake)
find_package(Python3 REQUIRED COMPONENTS Interpreter)
set(ENGLISH_HEADER "${CMAKE_CURRENT_SOURCE_DIR}/generated/translation/english_strings.h")
set(FULL_TRANSLATIONS "${CMAKE_CURRENT_SOURCE_DIR}/../translation/english-full.json")
if(NOT EXISTS "${FULL_TRANSLATIONS}")
    set(FULL_TRANSLATIONS "${CMAKE_CURRENT_SOURCE_DIR}/../translation/english.json")
endif()
set(FULL_HEADER "${CMAKE_CURRENT_SOURCE_DIR}/generated/translation/full_text.h")
set(ROSTER_HEADER "${CMAKE_CURRENT_SOURCE_DIR}/generated/translation/hanshin_names.h")
set(ALL_ROSTER_HEADER "${CMAKE_CURRENT_SOURCE_DIR}/generated/translation/all_roster_names.h")
add_custom_command(OUTPUT "${ALL_ROSTER_HEADER}"
    COMMAND "${Python3_EXECUTABLE}" "${CMAKE_CURRENT_SOURCE_DIR}/../tools/generate-all-roster-patch.py"
        "${CMAKE_CURRENT_SOURCE_DIR}/../translation/roster-names.json" "${ALL_ROSTER_HEADER}"
    DEPENDS "${CMAKE_CURRENT_SOURCE_DIR}/../tools/generate-all-roster-patch.py"
        "${CMAKE_CURRENT_SOURCE_DIR}/../translation/roster-names.json"
    VERBATIM)
add_custom_command(OUTPUT "${ROSTER_HEADER}"
    COMMAND "${Python3_EXECUTABLE}" "${CMAKE_CURRENT_SOURCE_DIR}/../tools/generate-roster-patch.py"
        "${CMAKE_CURRENT_SOURCE_DIR}/../translation/hanshin-roster.json" "${ROSTER_HEADER}"
    DEPENDS "${CMAKE_CURRENT_SOURCE_DIR}/../tools/generate-roster-patch.py"
        "${CMAKE_CURRENT_SOURCE_DIR}/../translation/hanshin-roster.json"
    VERBATIM)
add_custom_command(OUTPUT "${FULL_HEADER}"
    COMMAND "${Python3_EXECUTABLE}" "${CMAKE_CURRENT_SOURCE_DIR}/../tools/generate-full-text.py"
        "${FULL_TRANSLATIONS}" "${FULL_HEADER}"
    DEPENDS "${CMAKE_CURRENT_SOURCE_DIR}/../tools/generate-full-text.py" "${FULL_TRANSLATIONS}"
    VERBATIM)
add_custom_command(OUTPUT "${ENGLISH_HEADER}"
    COMMAND "${Python3_EXECUTABLE}" "${CMAKE_CURRENT_SOURCE_DIR}/../tools/generate-english.py"
        "${CMAKE_CURRENT_SOURCE_DIR}/../translation/english.json" "${ENGLISH_HEADER}"
    DEPENDS "${CMAKE_CURRENT_SOURCE_DIR}/../tools/generate-english.py"
        "${CMAKE_CURRENT_SOURCE_DIR}/../translation/english.json"
    VERBATIM)

# Sources
set(PROSPI3_SOURCES
    src/main.cpp
    src/english_patch.cpp
    src/diagnostics.cpp
    src/text_localization.cpp
    src/latin_font.cpp
    src/list_cleanup.cpp
    src/performance.cpp
    src/gpu_selection.cpp
    src/keyboard_taps.cpp
    "${ENGLISH_HEADER}"
    "${FULL_HEADER}"
    "${ROSTER_HEADER}"
    "${ALL_ROSTER_HEADER}"
)

if(WIN32)
    add_executable(prospi3 WIN32 ${PROSPI3_SOURCES})
else()
    add_executable(prospi3 ${PROSPI3_SOURCES})
endif()

rexglue_setup_target(prospi3 GPU_PLUGINS xenos)
target_include_directories(prospi3_recomp BEFORE PRIVATE "${CMAKE_CURRENT_SOURCE_DIR}/sdk-overrides")
if(WIN32)
    target_link_libraries(prospi3 PRIVATE gdi32 dxgi)
    target_link_options(prospi3 PRIVATE "-Wl,/MAP:${CMAKE_CURRENT_BINARY_DIR}/prospi3.map")
endif()
