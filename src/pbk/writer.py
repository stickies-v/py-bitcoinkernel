import ctypes
import typing

from pbk.capi.base import KernelOpaquePtr
import pbk.capi.bindings as k
from pbk.util.type import UserData


def _py_callback(
    c_bytes_ptr: ctypes.c_void_p, size: int, byte_writer_ptr: ctypes.c_void_p
):
    """C callback that receives serialized bytes and appends them to a ByteWriter buffer."""
    byte_writer: typing.Optional["ByteWriter"] = None
    try:
        byte_writer = UserData.from_void_ptr(byte_writer_ptr)
        assert byte_writer
        chunk = ctypes.string_at(c_bytes_ptr, size)
        byte_writer.buffer.extend(chunk)
        return 0
    except Exception as e:
        if byte_writer:
            byte_writer.exception = e
        return -1


class ByteWriter:
    """Buffer for collecting serialized bytes from C serialization functions."""

    def __init__(self):
        """Create a new byte writer with an empty buffer."""
        self.buffer = bytearray()
        self.exception = None

    def write(self, to_bytes_func: typing.Callable, obj: KernelOpaquePtr) -> bytes:
        """Serialize a kernel object to bytes using the provided C function."""
        self.buffer.clear()
        self.exception = None

        ret = to_bytes_func(obj, k.btck_WriteBytes(_py_callback), UserData(self))

        if ret != 0:
            if self.exception:
                raise self.exception
            raise RuntimeError(
                f"C serialization function failed with return code {ret}"
            )
        return bytes(self.buffer)
