import ctypes
import inspect
import logging
import re
import threading
import typing
from collections.abc import Callable
from contextlib import contextmanager
from datetime import datetime, timezone
from enum import IntEnum
from pathlib import Path

import pbk.capi.bindings as k
from pbk.capi import KernelOpaquePtr
from pbk.util.type import UserData


# bitcoinkernel's logging setters require external synchronization
LOGGING_LOCK = threading.RLock()


# TODO: add enum auto-generation or testing to ensure it remains in
# sync with bitcoinkernel.h
class LogCategory(IntEnum):
    """Logging categories for kernel messages.

    These categories allow fine-grained control over which types of log
    messages are enabled. Categories can be individually enabled or disabled.
    """

    ALL = 0  #: All log categories
    BENCH = 1  #: Benchmarking and performance metrics
    BLOCKSTORAGE = 2  #: Block storage operations
    COINDB = 3  #: Coin database operations
    LEVELDB = 4  #: LevelDB database operations
    MEMPOOL = 5  #: Memory pool (mempool) operations
    PRUNE = 6  #: Block pruning operations
    RAND = 7  #: Random number generation
    REINDEX = 8  #: Blockchain reindexing operations
    VALIDATION = 9  #: Block and transaction validation
    KERNEL = 10  #: General kernel operations


# TODO: add enum auto-generation or testing to ensure it remains in
# sync with bitcoinkernel.h
class LogLevel(IntEnum):
    """Log severity levels.

    These levels control the minimum severity of messages that will be logged.
    Setting a level filters out messages below that severity.

    Note:
        The TRACE level from bitcoinkernel is not exposed, as it is not
        natively supported by Python's logging library.
    """

    DEBUG = 1  #: Debug-level messages with detailed information
    INFO = 2  #: Informational messages about normal operations


KERNEL_LEVEL_TO_PYTHON = {  # numeric value
    LogLevel.INFO: logging.INFO,  # 20
    LogLevel.DEBUG: logging.DEBUG,  # 10
}


def btck_level_from_python(python_level: int) -> LogLevel:
    """Convert a Python logging level to a kernel LogLevel."""
    if python_level > KERNEL_LEVEL_TO_PYTHON[LogLevel.DEBUG]:
        return LogLevel.INFO
    return LogLevel.DEBUG


class LoggingOptions(k.btck_LoggingOptions):
    """Configuration options for log message formatting.

    These options control which metadata is included in log messages, such
    as timestamps, thread names, and source locations.
    """

    def __init__(
        self,
        log_timestamps: bool = True,
        log_time_micros: bool = False,
        log_threadnames: bool = False,
        log_sourcelocations: bool = False,
        always_print_category_levels: bool = False,
    ):
        """Create logging format options.

        Args:
            log_timestamps: If True, prepend a timestamp to log messages.
            log_time_micros: If True, use microsecond precision for timestamps.
            log_threadnames: If True, prepend the thread name to log messages.
            log_sourcelocations: If True, prepend the source file location to log messages.
            always_print_category_levels: If True, prepend the category and level to log messages.
        """
        super().__init__()
        self.log_timestamps = log_timestamps
        self.log_time_micros = log_time_micros
        self.log_threadnames = log_threadnames
        self.log_sourcelocations = log_sourcelocations
        self.always_print_category_levels = always_print_category_levels

    @property
    def _as_parameter_(self):
        """Return the ctypes reference for passing to C functions."""
        return ctypes.byref(self)


class SourceLocation:
    """Source code location information for a log entry.

    Represents the file, function, and line number where a log message
    originated. All fields are optional and may be None if the information
    was unavailable or logging of source locations was disabled.
    """

    def __init__(
        self,
        file: str | None = None,
        func: str | None = None,
        line: int | None = None,
    ):
        """Create a source location.

        Args:
            file: The source file path, or None if unavailable.
            func: The function name, or None if unavailable.
            line: The line number, or None if unavailable.
        """
        self.file = file
        self.func = func
        self.line = line

    def __str__(self) -> str:
        """Format the source location as a string.

        Returns a string like "file.cpp:123 (function_name)", omitting
        parts that are unavailable.
        """
        parts = []
        if self.file:
            if self.line:
                parts.append(f"{self.file}:{self.line}")
            else:
                parts.append(self.file)
        elif self.line:
            parts.append(f":{self.line}")

        if self.func:
            if parts:
                parts.append(f"({self.func})")
            else:
                parts.append(self.func)

        return " ".join(parts)

    def __repr__(self) -> str:
        return f"SourceLocation(file={self.file!r}, func={self.func!r}, line={self.line!r})"


class LogEntry(k.btck_LogEntry):
    """A structured log entry from the kernel.

    Provides Pythonic access to log entry fields including message,
    source location, timestamp, and metadata. This class wraps the
    C btck_LogEntry structure and converts raw fields to Python types.
    """

    @property
    def level(self) -> LogLevel:
        """The severity level of this log entry."""
        return LogLevel(super().level)

    @property
    def category(self) -> LogCategory:
        """The category this log entry belongs to."""
        return LogCategory(super().category)

    @property
    def message(self) -> str:
        """The log message text."""
        return ctypes.string_at(super().message, super().message_len).decode("utf-8")

    @property
    def source_location(self) -> SourceLocation:
        """The source code location where this log was generated."""
        file = None
        if super().source_file:
            file = ctypes.string_at(
                super().source_file, super().source_file_len
            ).decode("utf-8")

        func = None
        if super().source_func:
            func = ctypes.string_at(
                super().source_func, super().source_func_len
            ).decode("utf-8")

        line = super().source_line if super().source_line != 0 else None

        return SourceLocation(file=file, func=func, line=line)

    @property
    def timestamp(self) -> datetime:
        """The timestamp when this log was generated (UTC, timezone-aware)."""
        return datetime.fromtimestamp(
            super().timestamp_s + super().timestamp_us / 1_000_000,
            tz=timezone.utc,
        )

    @property
    def thread_name(self) -> str | None:
        """The name of the thread that generated this log, or None if unavailable."""
        if not super().thread_name:
            return None
        return ctypes.string_at(super().thread_name, super().thread_name_len).decode(
            "utf-8"
        )


def is_valid_log_callback(fn: typing.Any) -> bool:
    """Validate that a function matches the log callback signature.

    Performs a best-effort check that the function is callable and accepts
    exactly one parameter. Does not inspect parameter or return types.

    Args:
        fn: The function to validate.

    Returns:
        True if the function appears to be a valid log callback.
    """
    if not callable(fn):
        return False

    fn_sig = inspect.signature(fn)
    if len(fn_sig.parameters) != 1:
        return False

    return True


def logging_set_options(options: LoggingOptions) -> None:
    """Set formatting options for the global internal logger.

    This changes global settings that affect all existing LoggingConnection
    instances. The changes take effect immediately.

    Args:
        options: Logging format options to apply.
    """
    with LOGGING_LOCK:
        k.btck_logging_set_options(options)


def set_log_level_category(category: LogCategory, level: LogLevel) -> None:
    """Set the minimum log level for a category.

    This changes the minimum severity of messages that will be logged for
    the specified category. Affects all existing LoggingConnection instances.

    Note:
        This does not enable categories. Use `enable_log_category()` to start
        logging from a category. If LogCategory.ALL is chosen, sets both the
        global fallback log level and the level for the ALL category itself.

    Args:
        category: The log category to configure.
        level: The minimum log level for this category.
    """
    with LOGGING_LOCK:
        k.btck_logging_set_level_category(category, level)


def enable_log_category(category: LogCategory) -> None:
    """Enable logging for a category.

    Once enabled, log messages from this category will be passed to all
    LoggingConnection callbacks. If LogCategory.ALL is chosen, all
    categories will be enabled.

    Args:
        category: The log category to enable.
    """
    with LOGGING_LOCK:
        k.btck_logging_enable_category(category)


def disable_log_category(category: LogCategory) -> None:
    """Disable logging for a category.

    Once disabled, log messages from this category will no longer be passed
    to LoggingConnection callbacks. If LogCategory.ALL is chosen, all
    categories will be disabled.

    Args:
        category: The log category to disable.
    """
    with LOGGING_LOCK:
        k.btck_logging_disable_category(category)


class LoggingConnection(KernelOpaquePtr):
    """Connection that receives kernel log messages via a callback.

    A logging connection invokes a callback function for every log message
    produced by the kernel. The connection can be destroyed to stop receiving
    messages. Messages logged before the first connection is created are
    buffered (up to 1MB) and delivered when the connection is established.
    """

    _create_fn = k.btck_logging_connection_create
    _destroy_fn = k.btck_logging_connection_destroy

    def __init__(self, cb: typing.Callable[[str], None], user_data: UserData = None):
        """Create a logging connection with a callback.

        Args:
            cb: Callback function that accepts a single string parameter
                (the log message) and returns None.
            user_data: Optional user data to associate with the connection.

        Raises:
            TypeError: If the callback doesn't have the correct signature.
            RuntimeError: If the C constructor fails (propagated from base class).
        """
        if not is_valid_log_callback(cb):
            raise TypeError(
                "Log callback must be a callable with 1 string parameter and no return value."
            )
        self._cb = self._wrap_log_fn(cb)  # ensure lifetime
        self._user_data = user_data
        super().__init__(self._cb, user_data, k.btck_DestroyCallback())

    @staticmethod
    def _wrap_log_fn(fn: Callable[[str], None]):
        """Wrap a Python callback for use with the C logging API.

        Args:
            fn: Python callback function accepting a string.

        Returns:
            A C-compatible callback function.
        """

        def wrapped(user_data: None, message: bytes, message_len: int):
            """C callback wrapper that decodes the message and calls the Python function."""
            return fn(ctypes.string_at(message, message_len).decode("utf-8"))

        return k.btck_LogCallback(wrapped)


class KernelLogViewer:
    """Integration between bitcoinkernel logging and Python's logging module.

    KernelLogViewer bridges bitcoinkernel's logging system with Python's
    standard logging module. It creates a LoggingConnection that parses
    kernel log messages and forwards them to a Python Logger instance.

    Messages are organized by category, with each category getting its own
    child logger. For example, VALIDATION messages go to a logger named
    "bitcoinkernel.VALIDATION".

    Note:
        To see debug messages, both the kernel category must be enabled
        (via the `categories` parameter) and the Python logger level must
        be set to DEBUG or lower.
    """

    def __init__(
        self,
        name: str = "bitcoinkernel",
        categories: typing.List[LogCategory] | None = None,
    ):
        """Create a log viewer that forwards kernel logs to Python logging.

        Args:
            name: Name for the root logger. Defaults to "bitcoinkernel".
            categories: List of log categories to enable. If None or empty,
                no categories are enabled by default.
        """
        self.name = name
        self.categories = categories or []
        self._logger = logging.getLogger(name)

        # To simplify things, just set the level for to DEBUG for all
        # log categories. This shouldn't have any effect until categories
        # are actually enabled with enable_log_category.
        set_log_level_category(LogCategory.ALL, LogLevel.DEBUG)
        if categories is None:
            categories = []
        for category in categories:
            enable_log_category(category)
        self.conn = self._create_log_connection()

    def getLogger(self, category: LogCategory | None = None) -> logging.Logger:
        """Get the Python logger for a specific category.

        Args:
            category: The log category to get a logger for. If None, returns
                the root logger.

        Returns:
            A logging.Logger instance for the specified category.
        """
        if category:
            return self._logger.getChild(category.name.upper())
        return self._logger

    @contextmanager
    def temporary_categories(self, categories: typing.List[LogCategory]) -> None:
        """Context manager to temporarily enable log categories.

        Enables the specified categories for the duration of the context,
        then disables them when exiting. Categories that were enabled during
        initialization remain enabled.

        Args:
            categories: List of categories to temporarily enable.

        Yields:
            None
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
        """Create the internal logging connection.

        Sets up logging options and creates a connection that parses and
        forwards kernel messages to Python loggers.

        Returns:
            A LoggingConnection instance.
        """
        # TODO: avoid logging stuff the user doesn't need
        log_opts = LoggingOptions(
            log_timestamps=True,
            log_time_micros=False,
            log_threadnames=True,
            log_sourcelocations=True,
            always_print_category_levels=True,
        )
        logging_set_options(log_opts)
        conn = LoggingConnection(cb=self._create_log_callback(self.getLogger()))
        return conn

    @staticmethod
    def _create_log_callback(logger: logging.Logger) -> typing.Callable[[str], None]:
        """Create a callback that parses kernel logs and forwards to Python logger.

        Args:
            logger: The Python logger to forward parsed messages to.

        Returns:
            A callback function that accepts kernel log messages.
        """

        def callback(msg: str) -> None:
            """Parse and forward a kernel log message to the Python logger."""
            try:
                record = parse_btck_log_string(logger.name, msg)
                logger.handle(record)
            except ValueError:
                logging.getLogger().error(f"Failed to parse log message: {msg}")

        return callback


def parse_btck_log_string(logger_name: str, log_string: str) -> logging.LogRecord:
    """Parse a bitcoinkernel log message into a Python LogRecord.

    Extracts metadata from the kernel's log format and creates a Python
    LogRecord with appropriate fields set. The kernel log format includes
    timestamp, thread name, source location, function name, category, level,
    and message.

    Args:
        logger_name: Base name for the logger. Category will be appended.
        log_string: The raw log message string from the kernel.

    Returns:
        A LogRecord suitable for handling by Python's logging system.

    Raises:
        ValueError: If the log message doesn't match the expected format.
    """
    pattern = r"""
        ^([\d-]+T[\d:]+Z)              # timestamp
        \s+\[([^\]]+)\]                # threadname
        \s+\[([^\]]+)\]                # filepath:lineno
        \s+\[(.+)\]                    # filename/function
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
