import ctypes
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
    LOCK = k.kernel_LOG_LOCK
    MEMPOOL = k.kernel_LOG_MEMPOOL
    PRUNE = k.kernel_LOG_PRUNE
    RAND = k.kernel_LOG_RAND
    REINDEX = k.kernel_LOG_REINDEX
    VALIDATION = k.kernel_LOG_VALIDATION
    KERNEL = k.kernel_LOG_KERNEL


class LoggingOptions(k.kernel_LoggingOptions):
    log_timestamps: bool = True
    log_time_micros: bool = False
    log_threadnames: bool = False
    log_sourcelocations: bool = False
    always_print_category_levels: bool = False

    @property
    def _as_parameter_(self):
        return ctypes.byref(self)


def _simple_print(message: str):
    print(message, end="")


class LoggingConnection(KernelOpaquePtr):
    def __init__(self, cb=_simple_print, user_data=None, opts=LoggingOptions()):
        self._cb = self._wrap_log_fn(cb)  # ensure lifetime
        self._user_data = user_data
        super().__init__(self._cb, user_data, opts)

    @staticmethod
    def _wrap_log_fn(fn: Callable[[str], None]):
        def wrapped(user_data: None, message: bytes, message_len: int):
            return fn(ctypes.string_at(message, message_len).decode("utf-8"))

        return k.kernel_LogCallback(wrapped)
