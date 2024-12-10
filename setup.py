import ctypes.util
import shutil
import subprocess
import sys
from pathlib import Path

from setuptools import find_packages
from setuptools.command.build_ext import build_ext
from skbuild import setup

BITCOIN_DIR = Path("depend/bitcoin").resolve()

if sys.platform.startswith("win"):
    LIB_EXTENSION = ".dll"
elif sys.platform == "darwin":
    LIB_EXTENSION = ".dylib"
else:
    LIB_EXTENSION = ".so"


class BitcoinBuildCommand(build_ext):
    """Custom build command for building Bitcoin Core library and generating bindings"""

    def run(self):
        if lib_path := ctypes.util.find_library("bitcoinkernel"):
            print(
                f"bitcoinkernel library already installed at {lib_path}, skipping build."
            )
        else:
            self.build_bitcoin_lib()
        super().run()

    def build_bitcoin_lib(self):
        """Build the Bitcoin library using CMake with Ninja"""
        cmake_build_dir = Path(self.build_temp) / "bitcoin"
        cmake_build_dir.mkdir(exist_ok=True, parents=True)

        # Create the package's lib directory
        package_lib_dir = Path(self.build_lib) / "pbk" / "lib"
        package_lib_dir.mkdir(parents=True, exist_ok=True)

        cmake_args = [
            "cmake",
            str(BITCOIN_DIR.resolve()),
            f"-DCMAKE_LIBRARY_OUTPUT_DIRECTORY={package_lib_dir.absolute()}",
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
            subprocess.run(cmake_args, cwd=cmake_build_dir, check=True)
            subprocess.run(
                [
                    "cmake",
                    "--build",
                    ".",
                    "--config",
                    "Release",
                    "-j",
                ],
                cwd=cmake_build_dir,
                check=True,
            )

            print(f"Bitcoin library built successfully in {package_lib_dir}")

        except subprocess.CalledProcessError as e:
            print(f"Error building Bitcoin library: {e}")
            raise
        finally:
            if cmake_build_dir.exists():
                shutil.rmtree(cmake_build_dir)
                print(f"Cleaned up build directory: {cmake_build_dir}")


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
