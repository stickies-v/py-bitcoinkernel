import ctypes
import inspect
import logging
import re
import threading
import typing
from collections.abc import Callable
from contextlib import contextmanager
from datetime import datetime
from enum import IntEnum
from pathlib import Path

import pbk.capi.bindings as k
from pbk.capi import KernelOpaquePtr


# bitcoinkernel's logging setters require external synchronization
LOGGING_LOCK = threading.RLock()


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


def add_log_level_category(category: LogCategory, level: LogLevel) -> None:
    """
    Set the log level of the global internal logger. This does not
    enable the selected categories. Use `enable_log_category` to start
    logging from a specific, or all categories.
    """
    with LOGGING_LOCK:
        k.kernel_add_log_level_category(category, level)


def enable_log_category(category: LogCategory) -> None:
    """
    Enable a specific log category for the global internal logger.
    """
    with LOGGING_LOCK:
        k.kernel_enable_log_category(category)


def disable_log_category(category: LogCategory) -> None:
    """
    Disable a specific log category for the global internal logger.
    """
    with LOGGING_LOCK:
        k.kernel_disable_log_category(category)


class LoggingConnection(KernelOpaquePtr):
    """
    Example (note: `print` is not thread-safe.):

    ```py
    def cb(msg):
        print(msg, end="")
    log = LoggingConnection(cb=cb)
    ```
    """

    def __init__(
        self, cb: typing.Callable[[str], None], user_data=None, opts=LoggingOptions()
    ):
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
    """
    Pipes `bitcoinkernel` logging output into a named `logging.Logger`.

    `KernelLogViewer` wraps a `logging.Logger` object, which can be
    accessed through `logging.getLogger(name)` or through this class'
    `getLogger()` method.

    To prevent flooding logs and allow for fine-grained control,
    `bitcoinkernel` assigns a category to each debug log message. To
    view debug messages, initialize `KernelLogViewer` with a list of
    categories (e.g.
    `KernelLogViewer(categories=[pbk.LogCategory.VALIDATION])`) and
    ensure the `logging` level is set to `logging.DEBUG` or lower.

    A sublogger is created for each enabled category, and can be
    accessed via this class' `getLogger()` method.
    """

    def __init__(
        self,
        name: str = "bitcoinkernel",
        categories: typing.List[LogCategory] | None = None,
    ):
        self.name = name
        self.categories = categories or []
        self._logger = logging.getLogger(name)

        # To simplify things, just set the level for to DEBUG for all
        # log categories. This shouldn't have any effect until categories
        # are actually enabled with enable_log_category.
        add_log_level_category(LogCategory.ALL, LogLevel.DEBUG)
        if categories is None:
            categories = []
        for category in categories:
            enable_log_category(category)
        self.conn = self._create_log_connection()

    def getLogger(self, category: LogCategory | None = None) -> logging.Logger:
        if category:
            return self._logger.getChild(category.name.upper())
        return self._logger

    @contextmanager
    def temporary_categories(self, categories: typing.List[LogCategory]):
        """
        Context manager that temporary enables `categories`, and
        disables them again when the function exits. Categories that the
        `KernelLogViewer` were initialized with remain enabled either
        way.
        """
        [enable_log_category(category) for category in categories]
        try:
            yield
        finally:
            [
                disable_log_category(category)
                for category in categories
                if category not in self.categories
            ]

    def _create_log_connection(self) -> LoggingConnection:
        """TODO: avoid logging stuff the user doesn't need"""
        log_opts = LoggingOptions(
            log_timestamps=True,
            log_time_micros=False,
            log_threadnames=True,
            log_sourcelocations=True,
            always_print_category_levels=True,
        )
        conn = LoggingConnection(
            cb=self._create_log_callback(self.getLogger()), opts=log_opts
        )
        return conn

    @staticmethod
    def _create_log_callback(logger: logging.Logger) -> typing.Callable[[str], None]:
        def callback(msg: str) -> None:
            try:
                record = parse_kernel_log_string(logger.name, msg)
                logger.handle(record)
            except ValueError:
                logging.getLogger().error(f"Failed to parse log message: {msg}")

        return callback


def parse_kernel_log_string(logger_name: str, log_string: str) -> logging.LogRecord:
    pattern = r"""
        ^([\d-]+T[\d:]+Z)              # timestamp
        \s+\[([^\]]+)\]                # threadname
        \s+\[([^\]]+)\]                # filepath:lineno
        \s+\[([^\]]+)\]                # filename/function
        \s+\[([^:]+):([^\]]+)\]        # category:level
        \s+(.+)$                       # message
    """
    match = re.match(pattern, log_string, re.VERBOSE)
    if not match:
        raise ValueError(f"Log pattern matching failed: {log_string}")
    timestamp, thread_name, source_loc, func_name, category, level, message = (
        match.groups()
    )
    pathname, lineno = (
        source_loc.rsplit(":", 1) if ":" in source_loc else (source_loc, 0)
    )
    filename = Path(pathname).name
    if category.upper() != "ALL":
        logger_name += f".{category.upper()}"
    created = datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%SZ").timestamp()
    levels = {
        "debug": logging.DEBUG,
        "info": logging.INFO,
        "warning": logging.WARN,
        "error": logging.ERROR,
    }

    record = logging.makeLogRecord(
        {
            "name": logger_name,
            "levelno": levels.get(level.lower(), 0),
            "levelname": level.upper(),
            "filename": filename,
            "pathname": pathname,
            "lineno": int(lineno) if lineno and lineno.isdigit() else 0,
            "msg": message,
            "args": (),
            "exc_info": None,
            "funcName": func_name,
            "created": created,
            "threadName": thread_name,
        }
    )
    return record
