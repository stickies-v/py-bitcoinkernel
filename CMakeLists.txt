cmake_minimum_required(VERSION 3.15)
project(py-bitcoinkernel)

# ----------------------------------------
# 1. Define a configurable Bitcoin source directory
# ----------------------------------------
set(BITCOINKERNEL_SOURCE_DIR "${CMAKE_CURRENT_SOURCE_DIR}/depend/bitcoin" CACHE PATH "Path to Bitcoin source directory")

if(DEFINED ENV{BITCOINKERNEL_LIB})
    set(BITCOINKERNEL_PATH $ENV{BITCOINKERNEL_LIB})
else()
    find_library(BITCOINKERNEL_PATH bitcoinkernel)
endif()

if(BITCOINKERNEL_PATH)
    message(STATUS "Using existing bitcoinkernel library at ${BITCOINKERNEL_PATH}")
    if(NOT EXISTS ${BITCOINKERNEL_PATH})
        message(FATAL_ERROR "File at ${BITCOINKERNEL_PATH} does not exist")
    endif()
else()
    # Library not found, build from source
    message(STATUS "Building bitcoinkernel from source in ${BITCOINKERNEL_SOURCE_DIR}")

    # Ensure the submodule is present
    if(NOT EXISTS "${BITCOINKERNEL_SOURCE_DIR}/CMakeLists.txt")
        message(FATAL_ERROR "Bitcoin source not found in ${BITCOINKERNEL_SOURCE_DIR}. Please ensure the submodule is initialized or provide the correct path.")
    endif()

    # Configure and build bitcoinkernel
    set(BITCOIN_BUILD_DIR "${CMAKE_CURRENT_BINARY_DIR}/bitcoin")
    file(MAKE_DIRECTORY ${BITCOIN_BUILD_DIR})

    # Configure bitcoin build
    execute_process(
        COMMAND ${CMAKE_COMMAND} 
            -S "${BITCOINKERNEL_SOURCE_DIR}"
            -B "${BITCOIN_BUILD_DIR}"
            -DBUILD_SHARED_LIBS=ON
            -DBUILD_KERNEL_LIB=ON
            -DBUILD_BENCH=OFF
            -DBUILD_CLI=OFF
            -DBUILD_DAEMON=OFF
            -DBUILD_FOR_FUZZING=OFF
            -DBUILD_FUZZ_BINARY=OFF
            -DBUILD_GUI=OFF
            -DBUILD_KERNEL_TEST=OFF
            -DBUILD_TESTS=OFF
            -DBUILD_TX=OFF
            -DBUILD_UTIL=OFF
            -DBUILD_UTIL_CHAINSTATE=OFF
            -DBUILD_WALLET_TOOL=OFF
            -DENABLE_WALLET=OFF
            -DWITH_SQLITE=OFF
        RESULT_VARIABLE bitcoin_configure_result
    )
    if(NOT bitcoin_configure_result EQUAL 0)
        message(FATAL_ERROR "Failed to configure Bitcoin build")
    endif()

    # Build bitcoinkernel
    execute_process(
        COMMAND ${CMAKE_COMMAND} --build "${BITCOIN_BUILD_DIR}" --config Release -j
        RESULT_VARIABLE bitcoin_build_result
    )
    if(NOT bitcoin_build_result EQUAL 0)
        message(FATAL_ERROR "Failed to build bitcoinkernel")
    endif()

    # Set path to the newly built library
    if(WIN32)
        set(LIB_DIR "Release")
    else()
        set(LIB_DIR "")
    endif()
    set(BITCOINKERNEL_PATH "${BITCOIN_BUILD_DIR}/src/kernel/${LIB_DIR}${CMAKE_SHARED_LIBRARY_PREFIX}bitcoinkernel${CMAKE_SHARED_LIBRARY_SUFFIX}")

    if(NOT EXISTS ${BITCOINKERNEL_PATH})
        message(FATAL_ERROR "Built library not found at expected location: ${BITCOINKERNEL_PATH}")
    endif()
endif()

# Import the library as an IMPORTED target if built from source
if(NOT TARGET bitcoinkernel)
    add_library(bitcoinkernel SHARED IMPORTED)
    set_target_properties(bitcoinkernel PROPERTIES
        IMPORTED_LOCATION "${BITCOINKERNEL_PATH}"
    )
endif()

message(STATUS "Installing bitcoinkernel shared library")
install(FILES "${BITCOINKERNEL_PATH}"
        DESTINATION _libs
)
