import ctypes
import inspect
import typing
from collections.abc import Callable
from enum import IntEnum

import pbk.capi.bindings as k
from pbk.capi import KernelOpaquePtr


class LogCategory(IntEnum):
    ALL = k.kernel_LOG_ALL
    BENCH = k.kernel_LOG_BENCH
    BLOCKSTORAGE = k.kernel_LOG_BLOCKSTORAGE
    COINDB = k.kernel_LOG_COINDB
    LEVELDB = k.kernel_LOG_LEVELDB
    MEMPOOL = k.kernel_LOG_MEMPOOL
    PRUNE = k.kernel_LOG_PRUNE
    RAND = k.kernel_LOG_RAND
    REINDEX = k.kernel_LOG_REINDEX
    VALIDATION = k.kernel_LOG_VALIDATION
    KERNEL = k.kernel_LOG_KERNEL


class LoggingOptions(k.kernel_LoggingOptions):
    def __init__(
        self,
        log_timestamps=True,
        log_time_micros=False,
        log_threadnames=False,
        log_sourcelocations=False,
        always_print_category_levels=False,
    ):
        super().__init__()
        self.log_timestamps = log_timestamps
        self.log_time_micros = log_time_micros
        self.log_threadnames = log_threadnames
        self.log_sourcelocations = log_sourcelocations
        self.always_print_category_levels = always_print_category_levels

    @property
    def _as_parameter_(self):
        return ctypes.byref(self)


def _simple_print(message: str):
    print(message, end="")


def is_valid_log_callback(fn: typing.Any) -> bool:
    """
    Best-effort attempt to check that `fn` adheres to the
    kernel_LogCallback signature.

    It does not inspect the type of the parameter and return value.
    """
    if not callable(fn):
        return False

    fn_sig = inspect.signature(fn)
    if len(fn_sig.parameters) != 1:
        return False

    return True


class LoggingConnection(KernelOpaquePtr):
    def __init__(self, cb=_simple_print, user_data=None, opts=LoggingOptions()):
        if not is_valid_log_callback(cb):
            raise TypeError(
                "Log callback must be a callable with 1 string parameter and no return value."
            )
        self._cb = self._wrap_log_fn(cb)  # ensure lifetime
        self._user_data = user_data
        super().__init__(self._cb, user_data, opts)

    @staticmethod
    def _wrap_log_fn(fn: Callable[[str], None]):
        def wrapped(user_data: None, message: bytes, message_len: int):
            return fn(ctypes.string_at(message, message_len).decode("utf-8"))

        return k.kernel_LogCallback(wrapped)
