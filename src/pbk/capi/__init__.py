import warnings

# ctypeslib2 (up to v2.4.0) emits `_pack_` on generated structures without a
# companion `_layout_`. Python 3.14 deprecates this and 3.19 will reject it.
# The three affected structs in bindings.py have identical ms/gcc-sysv layouts
# under `_pack_=1`, so the implicit default is safe; silence the warning until
# ctypeslib2 gains `_layout_` support (no CLI/runtime knob exists today).
warnings.filterwarnings(
    "ignore",
    message=r"Due to '_pack_', the '.*' Structure will use memory layout.*",
    category=DeprecationWarning,
)

from pbk.capi.base import KernelOpaquePtr  # noqa: E402

__all__ = ["KernelOpaquePtr"]
