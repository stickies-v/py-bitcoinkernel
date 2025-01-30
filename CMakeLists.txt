cmake_minimum_required(VERSION 3.22)
project(py-bitcoinkernel
        VERSION 0.1)

# Set install prefix to be relative to the build directory
set(CMAKE_INSTALL_PREFIX "${CMAKE_BINARY_DIR}")

include(ExternalProject)

add_library(bitcoinkernel SHARED IMPORTED)
if(DEFINED ENV{BITCOINKERNEL_LIB})
    message(STATUS "Using bitcoinkernel library from BITCOINKERNEL_LIB: $ENV{BITCOINKERNEL_LIB}")
    set(BITCOINKERNEL_PATH "$ENV{BITCOINKERNEL_LIB}")
else()
    message(STATUS "Building bitcoinkernel from source in depend/bitcoin/")
    message(STATUS "Using toolchain for host: ${HOST_TUPLE}")

    if(NOT EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/depend/bitcoin/CMakeLists.txt")
        message(FATAL_ERROR "Bitcoin source not found in depend/bitcoin/. Please ensure the submodule is initialized.")
    endif()

    ExternalProject_Add(bitcoin_core
        SOURCE_DIR "${CMAKE_CURRENT_SOURCE_DIR}/depend/bitcoin"
        CMAKE_ARGS
            -DCMAKE_INSTALL_PREFIX=<INSTALL_DIR>
            -DCMAKE_INSTALL_LIBDIR=${CMAKE_INSTALL_LIBDIR}
            -DCMAKE_OSX_ARCHITECTURES=${CMAKE_OSX_ARCHITECTURES}
            -DCMAKE_OSX_DEPLOYMENT_TARGET=${CMAKE_OSX_DEPLOYMENT_TARGET}
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
        BUILD_COMMAND ${CMAKE_COMMAND} --build <BINARY_DIR> --target bitcoinkernel
        INSTALL_COMMAND
            ${CMAKE_COMMAND} --install <BINARY_DIR> --strip --component Kernel
    )

    # Create imported target for bitcoinkernel
    add_dependencies(bitcoinkernel bitcoin_core)

    ExternalProject_Get_Property(bitcoin_core INSTALL_DIR)
    set(RELATIVE_INSTALL_PATH "${CMAKE_INSTALL_LIBDIR}/libbitcoinkernel${CMAKE_SHARED_LIBRARY_SUFFIX}")
    if(BITCOIN_TARGET MATCHES ".*mingw.*" OR BITCOIN_TARGET MATCHES ".*windows.*")
        set(RELATIVE_INSTALL_PATH "bin/libbitcoinkernel.dll")
    endif()
    set(BITCOINKERNEL_PATH "${INSTALL_DIR}/${RELATIVE_INSTALL_PATH}")

endif()

set_target_properties(bitcoinkernel PROPERTIES
    IMPORTED_LOCATION "${BITCOINKERNEL_PATH}"
)

install(FILES "${BITCOINKERNEL_PATH}"
    DESTINATION "_libs"
    COMPONENT Kernel
)
