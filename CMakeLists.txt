cmake_minimum_required(VERSION 3.15)
project(py-bitcoinkernel
        VERSION 0.1)

# Set install prefix to be relative to the build directory
set(CMAKE_INSTALL_PREFIX "${CMAKE_BINARY_DIR}")

if(DEFINED ENV{BITCOINKERNEL_LIB})
    message(STATUS "Using bitcoinkernel library from BITCOINKERNEL_LIB: $ENV{BITCOINKERNEL_LIB}")
    add_library(bitcoinkernel SHARED IMPORTED)
    set_target_properties(bitcoinkernel PROPERTIES
        IMPORTED_LOCATION "$ENV{BITCOINKERNEL_LIB}"
    )
    
    # Install the imported library to _libs
    install(FILES "$ENV{BITCOINKERNEL_LIB}"
        DESTINATION "_libs"
        COMPONENT Kernel
    )
else()
    message(STATUS "Building bitcoinkernel from source in depend/bitcoin/")
    message(STATUS "Using toolchain for host: ${HOST_TUPLE}")

    if(NOT EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/depend/bitcoin/CMakeLists.txt")
        message(FATAL_ERROR "Bitcoin source not found in depend/bitcoin/. Please ensure the submodule is initialized.")
    endif()

    # Configure Bitcoin build options
    set(BUILD_SHARED_LIBS ON)
    set(BUILD_KERNEL_LIB ON)
    set(BUILD_BENCH OFF)
    set(BUILD_CLI OFF)
    set(BUILD_DAEMON OFF)
    set(BUILD_FOR_FUZZING OFF)
    set(BUILD_FUZZ_BINARY OFF)
    set(BUILD_GUI OFF)
    set(BUILD_KERNEL_TEST OFF)
    set(BUILD_TESTS OFF)
    set(BUILD_TX OFF)
    set(BUILD_UTIL OFF)
    set(BUILD_UTIL_CHAINSTATE OFF)
    set(BUILD_WALLET_TOOL OFF)
    set(ENABLE_WALLET OFF)
    set(WITH_SQLITE OFF)

    add_subdirectory(depend/bitcoin EXCLUDE_FROM_ALL)

    # Make bitcoinkernel part of the default build
    set_target_properties(bitcoinkernel PROPERTIES
        EXCLUDE_FROM_ALL FALSE
    )

    install(TARGETS bitcoinkernel
        COMPONENT Kernel
        LIBRARY DESTINATION "_libs"
        RUNTIME DESTINATION "_libs"
    )
endif()
