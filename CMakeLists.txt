cmake_minimum_required(VERSION 3.22)
project(py-bitcoinkernel
        VERSION 0.1)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED True)

include(ExternalProject)
include(GNUInstallDirs)

##############################################
# Configure and build bitcoinkernel dependency
##############################################

set(BITCOIN_TARGET "" CACHE STRING "Host triple for cross compilation, enables depends build if set")

set(BITCOIN_EXTERNAL_INSTALL_DIR ${CMAKE_BINARY_DIR}/bitcoin_core_install)
set(BITCOINKERNEL_LIBRARY_FILE "${BITCOIN_EXTERNAL_INSTALL_DIR}/${CMAKE_INSTALL_LIBDIR}/${CMAKE_STATIC_LIBRARY_PREFIX}bitcoinkernel${CMAKE_STATIC_LIBRARY_SUFFIX}")
set(BITCOINKERNEL_PC_FILE "${BITCOIN_EXTERNAL_INSTALL_DIR}/${CMAKE_INSTALL_LIBDIR}/pkgconfig/libbitcoinkernel.pc")

if(DEFINED ENV{BITCOINKERNEL_LIB})
    # This case implies that libbitcoinkernel and its .pc file are already installed
    # in a location findable by PkgConfig (e.g., system paths or PKG_CONFIG_PATH is set).
    # We'll proceed to the PkgConfig step directly.
    message(STATUS "Attempting to use pre-existing bitcoinkernel from environment (via PkgConfig)")
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
            LOG_BUILD 1
        )
        set(TOOLCHAIN_ARG "--toolchain" "${DEPENDS_DIR}/${BITCOIN_TARGET}/toolchain.cmake")
        set(BITCOIN_DEPENDS_ARG DEPENDS bitcoin_depends)
    endif()

    ExternalProject_Add(bitcoin_core
        ${BITCOIN_DEPENDS_ARG}
        SOURCE_DIR "${BITCOIN_SOURCE_DIR}"
        INSTALL_DIR "${BITCOIN_EXTERNAL_INSTALL_DIR}" # bitcoin_core installs here
        CONFIGURE_COMMAND ${CMAKE_COMMAND} ${TOOLCHAIN_ARG} <SOURCE_DIR>
            -DCMAKE_INSTALL_PREFIX=<INSTALL_DIR>
            -DCMAKE_INSTALL_LIBDIR=${CMAKE_INSTALL_LIBDIR}
            -DCMAKE_OSX_ARCHITECTURES=${CMAKE_OSX_ARCHITECTURES}
            -DCMAKE_OSX_DEPLOYMENT_TARGET=${CMAKE_OSX_DEPLOYMENT_TARGET}
            -DBUILD_SHARED_LIBS=OFF
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
        # Key byproducts are the main library and its .pc file
        BUILD_BYPRODUCTS
            "${BITCOINKERNEL_LIBRARY_FILE}"
            "${BITCOINKERNEL_PC_FILE}"
        BUILD_COMMAND ${CMAKE_COMMAND} --build <BINARY_DIR> --target libbitcoinkernel
        INSTALL_COMMAND ${CMAKE_COMMAND} --install <BINARY_DIR> --component libbitcoinkernel
        LOG_CONFIGURE 1
        LOG_BUILD 1
    )
    # Add dependency to ensure pbk_ext only tries to configure/build after bitcoin_core has run its install.
    # This is implicit for linking but good to be explicit if pkg_check_modules is used at configure time.
    # However, for a true two-step, pbk_ext's configuration happens in a *later* CMake run.
    # For now, we rely on the user re-running CMake if BITCOINKERNEL_FOUND is false initially.
endif()


########################################################
# Configure and build nanobind and the pbk_ext extension
########################################################

find_package(Python 3.8 COMPONENTS Interpreter Development.Module REQUIRED)

execute_process(
    COMMAND "${Python_EXECUTABLE}" -m nanobind --cmake_dir
    OUTPUT_STRIP_TRAILING_WHITESPACE OUTPUT_VARIABLE nanobind_ROOT
)
find_package(nanobind CONFIG REQUIRED HINTS "${nanobind_ROOT}")

find_package(PkgConfig REQUIRED)

# Set PKG_CONFIG_PATH to include the directory where libbitcoinkernel.pc will be installed.
# This is crucial for pkg_check_modules to find it.
# This needs to be set *before* pkg_check_modules is called.
# For the first CMake run, this path might not yet contain the .pc file.
set(ENV{PKG_CONFIG_PATH} "${BITCOIN_EXTERNAL_INSTALL_DIR}/${CMAKE_INSTALL_LIBDIR}/pkgconfig:$ENV{PKG_CONFIG_PATH}")

pkg_check_modules(BITCOINKERNEL QUIET libbitcoinkernel)

if(NOT BITCOINKERNEL_FOUND)
    message(WARNING "PKG_CONFIG_PATH: $ENV{PKG_CONFIG_PATH}")
    message(WARNING "libbitcoinkernel.pc not found. If bitcoin_core was just built, "
                    "please re-run CMake configuration. The build will likely fail.")
    # Define dummy variables to prevent CMake errors in nanobind_add_module if not found,
    # though the link step will fail.
    set(BITCOINKERNEL_INCLUDE_DIRS "")
    set(BITCOINKERNEL_LIBRARIES "")
else()
    message(STATUS "Found libbitcoinkernel via pkg-config:")
    message(STATUS "  BITCOINKERNEL_INCLUDE_DIRS: ${BITCOINKERNEL_INCLUDE_DIRS}")
    message(STATUS "  BITCOINKERNEL_LIBRARIES: ${BITCOINKERNEL_LIBRARIES}")
    message(STATUS "  BITCOINKERNEL_LIBRARY_DIRS: ${BITCOINKERNEL_LIBRARY_DIRS}")
    message(STATUS "  BITCOINKERNEL_LDFLAGS: ${BITCOINKERNEL_LDFLAGS}")
    message(STATUS "  BITCOINKERNEL_CFLAGS: ${BITCOINKERNEL_CFLAGS}")
endif()

nanobind_add_module(
    pbk_ext
    STABLE_ABI
    src/pbk_ext.cpp)

if(BITCOINKERNEL_FOUND)
    target_include_directories(pbk_ext PRIVATE ${BITCOINKERNEL_INCLUDE_DIRS})
    # BITCOINKERNEL_LIBRARIES from pkg-config typically includes full paths to .a files
    # or -L flags and -l flags.
    target_link_libraries(pbk_ext PRIVATE ${BITCOINKERNEL_LIBRARIES})
else()
    # If not found, we still declare the target_link_libraries to avoid CMake errors
    # about the target not being linked, but it will fail at link time.
    # Or, one could make pbk_ext an optional build.
    message(WARNING "pbk_ext will be built without linking libbitcoinkernel - this will fail at link time.")
endif()

# Ensure pbk_ext build waits for bitcoin_core to complete its install step.
# This is important because the .pc file and libraries become available after bitcoin_core's INSTALL_COMMAND.
if(NOT DEFINED ENV{BITCOINKERNEL_LIB})
    add_dependencies(pbk_ext bitcoin_core)
endif()

install(TARGETS pbk_ext LIBRARY DESTINATION pbk)
