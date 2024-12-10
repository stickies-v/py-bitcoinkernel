import ctypes

from pbk.capi import KernelPtr


class ByteArray(KernelPtr):
    @property
    def data(self) -> bytes:
        return ctypes.string_at(self.contents.data, self.contents.size)


class UserData:
    def __init__(self, data=None):
        self.c_void_p = None
        if data is not None:
            self._py_object = ctypes.py_object(data)
            self.c_void_p = ctypes.cast(
                ctypes.pointer(self._py_object), ctypes.c_void_p
            )

    @staticmethod
    def get(data_ptr):
        if data_ptr:
            return ctypes.cast(
                data_ptr, ctypes.POINTER(ctypes.py_object)
            ).contents.value
        return None
