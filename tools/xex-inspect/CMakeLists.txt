cmake_minimum_required(VERSION 3.25)
project(prospi3_inspection LANGUAGES CXX)
set(CMAKE_CXX_STANDARD 23)
find_package(rexglue 0.10.0 REQUIRED CONFIG)
find_package(Python3 REQUIRED COMPONENTS Interpreter)
get_filename_component(PORT_ROOT "${CMAKE_CURRENT_SOURCE_DIR}/../../prospi3-recomp" ABSOLUTE)
set(ENGLISH_HEADER "${PORT_ROOT}/generated/translation/english_strings.h")
add_custom_command(OUTPUT "${ENGLISH_HEADER}"
    COMMAND "${Python3_EXECUTABLE}" "${PORT_ROOT}/../tools/generate-english.py"
        "${PORT_ROOT}/../translation/english.json" "${ENGLISH_HEADER}"
    DEPENDS "${PORT_ROOT}/../tools/generate-english.py" "${PORT_ROOT}/../translation/english.json"
    VERBATIM)
add_executable(prospi3_inspect main.cpp "${PORT_ROOT}/src/english_patch.cpp" "${ENGLISH_HEADER}")
target_include_directories(prospi3_inspect PRIVATE "${PORT_ROOT}" "${PORT_ROOT}/src")
target_link_libraries(prospi3_inspect PRIVATE rex::runtime)
rexglue_apply_target_settings(prospi3_inspect)
add_custom_command(TARGET prospi3_inspect POST_BUILD
    COMMAND ${CMAKE_COMMAND} -E copy_if_different
    "$<TARGET_FILE:rex::runtime>" "$<TARGET_FILE_DIR:prospi3_inspect>" VERBATIM)
