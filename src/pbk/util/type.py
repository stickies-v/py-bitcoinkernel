import ctypes
from typing import Any, Optional


class UserData:
    """Wrapper for passing arbitrary Python objects through C void pointers."""

    def __init__(self, data: Optional[Any] = None) -> None:
        """Create a UserData wrapper.

        Args:
            data: Optional Python object to wrap.
        """
        self._py_object: Optional[ctypes.py_object] = None
        self._as_parameter_: Optional[ctypes.c_void_p] = None
        if data is not None:
            self._py_object = ctypes.py_object(data)
            self._as_parameter_ = ctypes.cast(
                ctypes.pointer(self._py_object), ctypes.c_void_p
            )

    @staticmethod
    def from_void_ptr(void_ptr: ctypes.c_void_p) -> Optional[Any]:
        """Extract a Python object from a C void pointer."""
        if void_ptr:
            return ctypes.cast(
                void_ptr, ctypes.POINTER(ctypes.py_object)
            ).contents.value
        return None
