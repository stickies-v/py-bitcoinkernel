cmake_minimum_required(VERSION 3.22)
project(py-bitcoinkernel
        VERSION 0.1)

# Set install prefix to be relative to the build directory
set(CMAKE_INSTALL_PREFIX "${CMAKE_BINARY_DIR}")

include(ExternalProject)
include(GNUInstallDirs)

set(BITCOIN_TARGET "" CACHE STRING "Host triple for cross compilation, enables depends build if set")

add_library(bitcoinkernel SHARED IMPORTED)
if(DEFINED ENV{BITCOINKERNEL_LIB})
    file(GLOB BITCOINKERNEL_MATCHES "$ENV{BITCOINKERNEL_LIB}")
    list(LENGTH BITCOINKERNEL_MATCHES MATCH_COUNT)
    if(NOT MATCH_COUNT EQUAL 1)
        message(FATAL_ERROR "Expected exactly one match for $ENV{BITCOINKERNEL_LIB}, found ${MATCH_COUNT}")
    endif()
    list(GET BITCOINKERNEL_MATCHES 0 BITCOINKERNEL_PATH)
else()
    set(BITCOIN_SOURCE_DIR "${CMAKE_CURRENT_SOURCE_DIR}/depend/bitcoin")
    message(STATUS "Building bitcoinkernel from source in ${BITCOIN_SOURCE_DIR}")

    if(NOT EXISTS "${BITCOIN_SOURCE_DIR}/CMakeLists.txt")
        message(FATAL_ERROR "Bitcoin source not found in ${BITCOIN_SOURCE_DIR}. Please ensure the submodule is initialized.")
    endif()

    if(BITCOIN_TARGET)
        set(DEPENDS_DIR "${BITCOIN_SOURCE_DIR}/depends")
        message(STATUS "Building Bitcoin Core dependencies for target: ${BITCOIN_TARGET}")
        ExternalProject_Add(bitcoin_depends
            SOURCE_DIR "${DEPENDS_DIR}"
            CONFIGURE_COMMAND ""
            BUILD_COMMAND make -C "${DEPENDS_DIR}"
                NO_QT=1 NO_QR=1 NO_ZMQ=1 NO_WALLET=1 NO_USDT=1 
                NO_LIBEVENT=1 NO_SQLITE=1 NO_BDB=1 
                HOST=${BITCOIN_TARGET} -j${CMAKE_BUILD_PARALLEL_LEVEL}
            BUILD_IN_SOURCE 1
            INSTALL_COMMAND ""
        )
        set(TOOLCHAIN_ARG "--toolchain" "${DEPENDS_DIR}/${BITCOIN_TARGET}/toolchain.cmake")
        set(BITCOIN_DEPENDS_ARG DEPENDS bitcoin_depends)
    endif()

    ExternalProject_Add(bitcoin_core
        ${BITCOIN_DEPENDS_ARG}
        SOURCE_DIR "${BITCOIN_SOURCE_DIR}"
        CONFIGURE_COMMAND ${CMAKE_COMMAND} ${TOOLCHAIN_ARG} <SOURCE_DIR>
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
