cmake_minimum_required(VERSION 3.15)
project(obfuscator LANGUAGES C CXX)

find_package(LLVM REQUIRED CONFIG)

message(STATUS "Found LLVM ${LLVM_PACKAGE_VERSION}")
message(STATUS "Using LLVMConfig.cmake in: ${LLVM_DIR}")

include_directories(${LLVM_INCLUDE_DIRS})
add_definitions(${LLVM_DEFINITIONS})

add_executable(obfuscator src/main.cpp)

llvm_map_components_to_libnames(LLVM_LIBS support)

target_link_libraries(obfuscator ${LLVM_LIBS})

