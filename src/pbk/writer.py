import ctypes
import typing

from pbk.capi.base import KernelPtr
import pbk.capi.bindings as k
from pbk.util.type import UserData


def _py_callback(
    c_bytes_ptr: ctypes.c_void_p, size: int, byte_writer_ptr: ctypes.c_void_p
):
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
    def __init__(self):
        self.buffer = bytearray()
        self.exception = None

    def write(self, to_bytes_func: typing.Callable, obj: KernelPtr) -> bytes:
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
