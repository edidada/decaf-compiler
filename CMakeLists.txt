cmake_minimum_required(VERSION 3.12)
project(decaf-compiler LANGUAGES C CXX)

set(CMAKE_CXX_STANDARD 11)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# --- Find Flex and Bison ---
find_package(FLEX REQUIRED)
find_package(BISON REQUIRED)

# --- Bison: parser.y -> y.tab.c + y.tab.h ---
BISON_TARGET(DecafParser
    ${CMAKE_SOURCE_DIR}/src/parser.y
    ${CMAKE_CURRENT_BINARY_DIR}/y.tab.c
    DEFINES_FILE ${CMAKE_CURRENT_BINARY_DIR}/y.tab.h
    COMPILE_FLAGS "-d -v -t"
)

# --- Flex: scanner.l -> lex.yy.c ---
FLEX_TARGET(DecafScanner
    ${CMAKE_SOURCE_DIR}/src/scanner.l
    ${CMAKE_CURRENT_BINARY_DIR}/lex.yy.c
)

# Flex depends on the parser header for token definitions
ADD_FLEX_BISON_DEPENDENCY(DecafScanner DecafParser)

# The generated .c files include C++ headers, so compile them as C++
set_source_files_properties(
    ${CMAKE_CURRENT_BINARY_DIR}/lex.yy.c
    ${CMAKE_CURRENT_BINARY_DIR}/y.tab.c
    PROPERTIES LANGUAGE CXX
)

# --- Source files (matches the Makefile SRCS list) ---
set(DECAF_SOURCES
    src/ast.cc
    src/ast_decl.cc
    src/ast_expr.cc
    src/ast_stmt.cc
    src/ast_type.cc
    src/codegen.cc
    src/errors.cc
    src/main.cc
    src/mips.cc
    src/symtab.cc
    src/tac.cc
    src/utility.cc
)

# --- Build the dcc compiler executable ---
add_executable(dcc
    ${DECAF_SOURCES}
    ${FLEX_DecafScanner_OUTPUTS}
    ${BISON_DecafParser_OUTPUTS}
)

target_include_directories(dcc PRIVATE
    ${CMAKE_SOURCE_DIR}/src
    ${CMAKE_CURRENT_BINARY_DIR}   # for y.tab.h, lex.yy.c
)

# Match Makefile warning flags and handle platform-specific issues
if(MSVC)
    target_compile_options(dcc PRIVATE /W1)
    # Tell flex-generated code not to include unistd.h (not available on Windows)
    # Suppress warnings about deprecated POSIX functions (vsprintf, etc.)
    target_compile_definitions(dcc PRIVATE YY_NO_UNISTD_H _CRT_SECURE_NO_WARNINGS)
else()
    target_compile_options(dcc PRIVATE -Wall -Wno-unused -Wno-sign-compare)
endif()

# --- Testing ---
enable_testing()
find_package(Python3 REQUIRED)
add_test(
    NAME decaf-tests
    COMMAND ${CMAKE_COMMAND} -E env "DCC=$<TARGET_FILE:dcc>"
            ${Python3_EXECUTABLE} ${CMAKE_SOURCE_DIR}/tests/run_tests.py
            ${CMAKE_SOURCE_DIR}/tests
)
