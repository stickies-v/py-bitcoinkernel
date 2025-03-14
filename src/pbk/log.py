import ctypes
import inspect
import logging
import re
import typing
from collections.abc import Callable
from datetime import datetime
from enum import IntEnum

import pbk.capi.bindings as k
from pbk.capi import KernelOpaquePtr


class LogCategory(IntEnum):
    ALL = k.kernel_LOG_ALL
    BENCH = k.kernel_LOG_BENCH
    BLOCKSTORAGE = k.kernel_LOG_BLOCKSTORAGE
    COINDB = k.kernel_LOG_COINDB
    LEVELDB = k.kernel_LOG_LEVELDB
    #  LOCK = k.kernel_LOG_LOCK  BCLog::LOCK only exists when compiled with DEBUG_LOCKCONTENTION, disable for now
    MEMPOOL = k.kernel_LOG_MEMPOOL
    PRUNE = k.kernel_LOG_PRUNE
    RAND = k.kernel_LOG_RAND
    REINDEX = k.kernel_LOG_REINDEX
    VALIDATION = k.kernel_LOG_VALIDATION
    KERNEL = k.kernel_LOG_KERNEL


class LogLevel(IntEnum):
    INFO = k.kernel_LOG_INFO
    DEBUG = k.kernel_LOG_DEBUG
    #  TRACE = k.kernel_LOG_TRACE  # TRACE is not a python-native logging level, disable it for now


KERNEL_LEVEL_TO_PYTHON = {  # numeric value
    LogLevel.INFO: logging.INFO,  # 20
    LogLevel.DEBUG: logging.DEBUG,  # 10
}


def kernel_level_from_python(python_level: int) -> LogLevel:
    if python_level > KERNEL_LEVEL_TO_PYTHON[LogLevel.DEBUG]:
        return LogLevel.INFO
    return LogLevel.DEBUG


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


def add_log_level_category(category: LogCategory, level: LogLevel) -> bool:
    """
    Set the log level of the global internal logger. This does not
    enable the selected categories. Use `enable_log_category` to start
    logging from a specific, or all categories.
    """
    return k.kernel_add_log_level_category(category, level)


def enable_log_category(category: LogCategory) -> bool:
    """
    Enable a specific log category for the global internal logger.
    """
    return k.kernel_enable_log_category(category)


def disable_log_category(category: LogCategory) -> bool:
    """
    Disable a specific log category for the global internal logger.
    """
    return k.kernel_disable_log_category(category)


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


class KernelLogViewer:
    def __init__(
        self,
        name: str = "bitcoinkernel",
        categories: typing.List[LogCategory] | None = None,
    ):
        self.name = name
        self._logger = logging.getLogger(f"{name}.{LogCategory.ALL.name.upper()}")

        if categories is None:
            categories = []
        for category in categories:
            self._sync_kernel_logging(category)
            self.enable_category(category)
        self.conn = self.create_log_connection()

    def getLogger(self, category: LogCategory | None = None) -> logging.Logger:
        if category:
            return self._logger.getChild(category.name.upper())
        return self._logger

    def handle(self, msg: str):
        record = self.parse_kernel_log_string(msg)
        self._logger.handle(record)

    def enable_category(self, category: LogCategory):
        enable_log_category(category)

    def disable_category(self, category: LogCategory):
        disable_log_category(category)

    def parse_kernel_log_string(self, log_string: str) -> logging.LogRecord:
        # pattern: <timestamp> [threadname] [filepath:lineno] [filename] [category:level] <msg>
        pattern = r"^([\d-]+T[\d:]+Z) \[([^\]]+)\] \[([^\]]+)\] \[([^\]]+)\] \[([^:]+):([^\]]+)\] (.+)$"
        match = re.match(pattern, log_string)
        assert match, f"Log pattern matching failed: {log_string}"
        timestamp, thread_name, source_loc, func_name, category, level, message = (
            match.groups()
        )
        pathname, lineno = (
            source_loc.rsplit(":", 1) if ":" in source_loc else (source_loc, 0)
        )
        created = datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%SZ").timestamp()
        kernel_level = LogLevel[level.upper()]
        level_num = KERNEL_LEVEL_TO_PYTHON[kernel_level]

        record = logging.makeLogRecord(
            {
                "name": f"{self.name}.{category.upper()}",
                "levelno": level_num,
                "levelname": level.upper(),
                "pathname": pathname,
                "lineno": int(lineno) if lineno and lineno.isdigit() else 0,
                "msg": message,
                "args": (),
                "exc_info": None,
                "func": func_name,
                "created": created,
                "threadName": thread_name,
            }
        )
        return record

    def create_log_connection(self) -> LoggingConnection:
        log_opts = LoggingOptions(
            log_timestamps=True,
            log_time_micros=False,
            log_threadnames=True,
            log_sourcelocations=True,
            always_print_category_levels=True,
        )
        conn = LoggingConnection(cb=self.handle, opts=log_opts)
        return conn

    def _sync_kernel_logging(self, category: LogCategory):
        logger = self._logger.getChild(category.name.upper())
        python_level = logger.getEffectiveLevel()
        kernel_level = kernel_level_from_python(python_level)
        if python_level > logging.DEBUG:
            logging.getLogger().warning(
                f"LogCategory {category.name.upper()} is set, but won't log anything unless global loglevel is set to DEBUG."
            )
        assert add_log_level_category(category, kernel_level)
