cmake_minimum_required(VERSION 3.15)
project(obfuscator LANGUAGES C CXX)

# ---------------------------
# C++ Standard
# ---------------------------
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# ---------------------------
# Build type default
# ---------------------------
if(NOT CMAKE_BUILD_TYPE)
    set(CMAKE_BUILD_TYPE Debug CACHE STRING "Build type" FORCE)
endif()

# ---------------------------
# Find LLVM
# ---------------------------
find_package(LLVM REQUIRED CONFIG)

message(STATUS "Found LLVM ${LLVM_PACKAGE_VERSION}")
message(STATUS "Using LLVMConfig.cmake in: ${LLVM_DIR}")

# ---------------------------
# LLVM definitions & includes
# ---------------------------
include_directories(${LLVM_INCLUDE_DIRS})
separate_arguments(LLVM_DEFINITIONS_LIST NATIVE_COMMAND "${LLVM_DEFINITIONS}")
add_definitions(${LLVM_DEFINITIONS_LIST})

# ---------------------------
# Source files
# ---------------------------
set(SOURCE_FILES
    src/main.cpp
    src/passes/BogusControlFlowPass.cpp
    src/passes/StringObfuscationPass.cpp
    src/passes/FakeLoopPass.cpp
    src/utils/ReportGenerator.cpp
)

# ---------------------------
# Executable
# ---------------------------
add_executable(obfuscator ${SOURCE_FILES})

# ---------------------------
# LLVM Components to link
# ---------------------------
llvm_map_components_to_libnames(
    LLVM_LIBS
    core
    support
    irreader
    passes
    analysis
    transformutils
    scalaropts
    instcombine
    bitreader
    bitwriter
    asmparser
)

# ---------------------------
# Link LLVM
# ---------------------------
target_link_libraries(obfuscator PRIVATE ${LLVM_LIBS})

# ---------------------------
# Include directories (target-scoped)
# ---------------------------
target_include_directories(obfuscator PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}/src
    ${CMAKE_CURRENT_SOURCE_DIR}/src/passes
    ${CMAKE_CURRENT_SOURCE_DIR}/src/utils
)