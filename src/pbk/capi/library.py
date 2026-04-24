import ctypes
import site
from importlib import resources
from pathlib import Path


def _find_bitcoinkernel_lib() -> str:
    resources_paths = [resources.files("pbk")]
    # Adding site packages makes this work in editable mode with scikit-build-core
    site_packages_paths = [Path(p) / "pbk" for p in site.getsitepackages()]
    for pkg_path in [*resources_paths, *site_packages_paths]:
        matches = list((pkg_path / "_libs").glob("*bitcoinkernel*"))  # ty: ignore[unresolved-attribute]
        if len(matches) == 1:
            return str(matches[0])
        if matches:
            raise RuntimeError(f"Found multiple libbitcoinkernel candidates: {matches}")
    raise RuntimeError("Could not find libbitcoinkernel. Please re-run `pip install`.")


BITCOINKERNEL_LIB = ctypes.CDLL(_find_bitcoinkernel_lib())
