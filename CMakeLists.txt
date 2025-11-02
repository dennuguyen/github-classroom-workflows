cmake_minimum_required(VERSION 3.31.6)
project(hello_project VERSION 1.0)

set(CMAKE_CXX_STANDARD 23)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

include(CTest)
enable_testing()

find_package(GTest REQUIRED)
include(GoogleTest)

option(ENABLE_SANITIZERS "Enable Address/Leak/UndefinedBehavior sanitizers" ON)
set(SANITIZE_FLAGS "-fsanitize=address,undefined,pointer-compare,pointer-subtract")

macro(build_gtest_suite TEST)
    add_executable(${TEST} ${TEST}.cpp)
    if(ENABLE_SANITIZERS)
        target_compile_options(${TEST} PRIVATE ${SANITIZE_FLAGS})
        target_link_options(${TEST} PRIVATE ${SANITIZE_FLAGS})
    endif()
    target_link_libraries(${TEST} GTest::gtest_main)
    gtest_discover_tests(${TEST})

    file(WRITE "${CMAKE_BINARY_DIR}/.env"
        "CMAKE_CURRENT_BINARY_DIR=${CMAKE_CURRENT_BINARY_DIR}\n"
        "CMAKE_CURRENT_SOURCE_DIR=${CMAKE_CURRENT_SOURCE_DIR}\n"
        "CMAKE_BINARY_DIR=${CMAKE_BINARY_DIR}\n"
        "CMAKE_SOURCE_DIR=${CMAKE_SOURCE_DIR}\n"
    )
endmacro()

add_subdirectory(test)