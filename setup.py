import subprocess
import sys
from pathlib import Path
import shutil
import os

from setuptools.command.build_ext import build_ext
from skbuild import setup
from setuptools import find_packages

# Directory constants
ARTIFACTS_DIR = Path("artifacts").resolve()
LIB_DIR = ARTIFACTS_DIR / "lib"
BITCOIN_DIR = Path("depend/bitcoin").resolve()
BUILD_DIR = Path("build") / "bitcoin"
HEADER_FILE = BITCOIN_DIR / "src/kernel/bitcoinkernel.h"
SRC_DIR = Path("src")
BINDINGS_FILE = SRC_DIR / "pbk" / "capi" / "bindings.py"

# Platform-specific settings
if sys.platform.startswith('win'):
    LIB_EXTENSION = '.dll'
elif sys.platform == 'darwin':
    LIB_EXTENSION = '.dylib'
else:
    LIB_EXTENSION = '.so'

class BitcoinBuildCommand(build_ext):
    """Custom build command for building Bitcoin Core library and generating bindings"""

    def run(self):
        ARTIFACTS_DIR.mkdir(exist_ok=True)
        LIB_DIR.mkdir(exist_ok=True)

        self.build_bitcoin_lib()
        self.copy_library_to_package()
        self.generate_bindings()
        super().run()

    def build_bitcoin_lib(self):
        """Build the Bitcoin library using CMake with Ninja"""
        BUILD_DIR.mkdir(exist_ok=True, parents=True)
        cmake_args = [
            "cmake",
            str(BITCOIN_DIR.resolve()),
            f"-DCMAKE_LIBRARY_OUTPUT_DIRECTORY={LIB_DIR.absolute()}",
            "-DBUILD_SHARED_LIBS=ON",
            "-DBUILD_KERNEL_LIB=ON",
            "-DBUILD_BENCH=OFF",
            "-DBUILD_CLI=OFF",
            "-DBUILD_DAEMON=ON",
            "-DBUILD_FOR_FUZZING=OFF",
            "-DBUILD_FUZZ_BINARY=OFF",
            "-DBUILD_GUI=OFF",
            "-DBUILD_KERNEL_TEST=OFF",
            "-DBUILD_TESTS=OFF",
            "-DBUILD_TX=OFF",
            "-DBUILD_UTIL=OFF",
            "-DBUILD_UTIL_CHAINSTATE=OFF",
            "-DBUILD_WALLET_TOOL=OFF",
            "-DENABLE_WALLET=OFF",
        ]

        # Try to use Ninja if available
        try:
            subprocess.run(["ninja", "--version"], check=True, stdout=subprocess.PIPE)
            cmake_args.append("-GNinja")
        except FileNotFoundError:
            print("Ninja not found, falling back to default generator")
        
        try:
            subprocess.run(cmake_args, cwd=BUILD_DIR, check=True)
            subprocess.run([
                "cmake",
                "--build", ".",
                "--config", "Release",
                "-j",
            ], cwd=BUILD_DIR, check=True)
            
            print(f"Bitcoin library built successfully in {LIB_DIR}")
            
        except subprocess.CalledProcessError as e:
            print(f"Error building Bitcoin library: {e}")
            raise
        finally:
            if BUILD_DIR.exists():
                shutil.rmtree(BUILD_DIR)
                print(f"Cleaned up build directory: {BUILD_DIR}")

    def copy_library_to_package(self):
        """Copy the built library to the package directory"""
        # Create the package's shared library directory
        package_lib_dir = Path(self.build_lib) / "pbk" / "lib"
        package_lib_dir.mkdir(parents=True, exist_ok=True)

        # Copy the library file
        lib_name = f"libbitcoinkernel{LIB_EXTENSION}"
        src_lib = LIB_DIR / lib_name
        dst_lib = package_lib_dir / lib_name

        if not src_lib.exists():
            raise FileNotFoundError(f"Library not found: {src_lib}")

        shutil.copy2(src_lib, dst_lib)
        print(f"Copied library to {dst_lib}")

    def generate_bindings(self):
        """Generate Python bindings using clang2py"""
        try:
            subprocess.run(["clang2py", "--version"], check=True, stdout=subprocess.PIPE)
        except FileNotFoundError:
            raise RuntimeError("clang2py is not installed. Please install it with 'pip install ctypeslib2'.")

        if not HEADER_FILE.exists():
            raise FileNotFoundError(f"Header file not found: {HEADER_FILE}")

        shared_library_path = LIB_DIR / f"libbitcoinkernel{LIB_EXTENSION}"
        if not shared_library_path.exists():
            raise FileNotFoundError(f"Shared library not found: {shared_library_path}")

        # Create the capi directory if it doesn't exist
        bindings_dir = Path(self.build_lib) / "pbk" / "capi"
        bindings_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate bindings to the build directory instead of source
        bindings_file = bindings_dir / "bindings.py"
        
        # Use relative path for the library
        relative_lib_path = os.path.join('lib', f'libbitcoinkernel{LIB_EXTENSION}')
        
        print(f"Generating bindings from {HEADER_FILE}...")
        clang2py_args = [
                "clang2py",
                str(HEADER_FILE),
                "-l", relative_lib_path,
                "-o", str(bindings_file)
             ]
        if sys.platform == 'darwin':
            clang2py_args.append("--nm")
            clang2py_args.append(str(ARTIFACTS_DIR.parent / "nm_patch.py"))

        subprocess.run(
            clang2py_args,
            check=True
        )
        print(f"Bindings generated at {bindings_file}")


setup(
    name="py-bitcoinkernel",
    packages=find_packages("src"),
    package_dir={"": "src"},
    package_data={
        "pbk": ["lib/*"],  # Include all files in the lib directory
    },
    cmake_source_dir=str(BITCOIN_DIR),
    cmdclass={
        "build_ext": BitcoinBuildCommand,
    },
)
