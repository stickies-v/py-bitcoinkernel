import ctypes
import inspect
import logging
import typing
from collections.abc import Callable
from dataclasses import dataclass
from enum import IntEnum
from pathlib import Path

import pbk.capi.bindings as k
from pbk.capi import KernelOpaquePtr


# TODO: add enum auto-generation or testing to ensure it remains in
# sync with bitcoinkernel.h
class LogCategory(IntEnum):
    """Logging categories for kernel messages.

    Every log entry carries a category, which can be used to filter or
    route entries. With [KernelLogViewer][pbk.KernelLogViewer], each
    category is forwarded to its own child logger.
    """

    NONE = 0
    """Not tied to a specific category, e.g. most INFO, WARNING and ERROR entries."""

    BENCH = 1
    """Benchmarking and performance metrics"""

    BLOCKSTORAGE = 2
    """Block storage operations"""

    COINDB = 3
    """Coin database operations"""

    LEVELDB = 4
    """LevelDB database operations"""

    MEMPOOL = 5
    """Memory pool (mempool) operations"""

    PRUNE = 6
    """Block pruning operations"""

    RAND = 7
    """Random number generation"""

    REINDEX = 8
    """Blockchain reindexing operations"""

    VALIDATION = 9
    """Block and transaction validation"""

    KERNEL = 10
    """General kernel operations"""

    TXPACKAGES = 11
    """Transaction package operations"""

    LOCK = 12
    """Lock contention"""


# TODO: add enum auto-generation or testing to ensure it remains in
# sync with bitcoinkernel.h
class LogLevel(IntEnum):
    """Log severity levels."""

    TRACE = 0
    """Very detailed messages, more verbose than DEBUG"""

    DEBUG = 1
    """Debug-level messages with detailed information"""

    INFO = 2
    """Informational messages about normal operations"""

    WARNING = 3
    """Unexpected events that do not prevent operation"""

    ERROR = 4
    """Errors that prevent an operation from completing"""


KERNEL_LEVEL_TO_PYTHON = {  # numeric value
    LogLevel.TRACE: logging.DEBUG - 5,  # 5
    LogLevel.DEBUG: logging.DEBUG,  # 10
    LogLevel.INFO: logging.INFO,  # 20
    LogLevel.WARNING: logging.WARNING,  # 30
    LogLevel.ERROR: logging.ERROR,  # 40
}


def _decode(ptr: typing.Any, length: int) -> str:
    """Copy a non-null-terminated C string into a Python string."""
    return ctypes.string_at(ptr, length).decode("utf-8", errors="replace")


@dataclass(frozen=True)
class LogEntry:
    """A log entry produced by the kernel.

    All fields are copied from the kernel, so a `LogEntry` remains valid
    after the logging callback returns.

    Attributes:
        message: Log message text. Not escaped, so it may contain newlines
            and other control characters.
        thread_name: Name of the thread that produced the entry.
        timestamp_ns: Wall-clock time when the entry was logged, in
            nanoseconds since the Unix epoch.
        mocktime_s: Mock time in effect when the entry was logged, in seconds
            since the Unix epoch, or 0 if no mock time is set.
        file_name: Name of the source file that produced the entry.
        function_name: Name of the function that produced the entry.
        line: Line number of the source code that produced the entry.
        level: Severity level of the entry.
        category: Category of the entry.
    """

    message: str
    thread_name: str
    timestamp_ns: int
    mocktime_s: int
    file_name: str
    function_name: str
    line: int
    level: LogLevel
    category: LogCategory

    @classmethod
    def _from_c(cls, entry: k.btck_LogEntry) -> "LogEntry":
        """Copy a C log entry into a new LogEntry."""
        return cls(
            message=_decode(entry.message, entry.message_len),
            thread_name=_decode(entry.thread_name, entry.thread_name_len),
            timestamp_ns=entry.timestamp_ns,
            mocktime_s=entry.mocktime_s,
            file_name=_decode(entry.file_name, entry.file_name_len),
            function_name=_decode(entry.function_name, entry.function_name_len),
            line=entry.line,
            level=LogLevel(entry.level),
            category=LogCategory(entry.category),
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
    return len(fn_sig.parameters) == 1


def logging_set_min_level(level: LogLevel) -> None:
    """Set the minimum level of log entries delivered to logging callbacks.

    Entries below this level are not delivered. The kernel default is
    `LogLevel.INFO`. This changes a global setting that affects all existing
    LoggingConnection instances.

    Args:
        level: The minimum log level.
    """
    k.btck_logging_set_min_level(level)


class LoggingConnection(KernelOpaquePtr):
    """Connection that receives kernel log entries via a callback.

    A logging connection invokes a callback function for every log entry
    at or above the [minimum level][pbk.logging_set_min_level] that the
    kernel produces while the connection exists. Entries logged before the
    connection is created are not delivered.

    The callback may be invoked from any kernel thread, but never
    concurrently. It blocks every kernel thread that logs, so it should
    return quickly. It must not call into the kernel, as this may deadlock.
    """

    _create_fn = k.btck_logging_connection_create
    _destroy_fn = k.btck_logging_connection_destroy

    def __init__(self, cb: Callable[[LogEntry], None]):
        """Create a logging connection with a callback.

        Args:
            cb: Callback function that accepts a single
                [LogEntry][pbk.LogEntry] parameter and returns None.

        Raises:
            TypeError: If the callback doesn't have the correct signature.
            RuntimeError: If the C constructor fails (propagated from base class).
        """
        if not is_valid_log_callback(cb):
            raise TypeError(
                "Log callback must be a callable with 1 LogEntry parameter and no return value."
            )
        self._cb = self._wrap_log_fn(cb)  # ensure lifetime
        super().__init__(self._cb, ctypes.c_void_p(), k.btck_DestroyCallback())

    @staticmethod
    def _wrap_log_fn(fn: Callable[[LogEntry], None]) -> k.btck_LogCallback:  # ty: ignore[invalid-type-form]
        """Wrap a Python callback for use with the C logging API.

        Args:
            fn: Python callback function accepting a LogEntry.

        Returns:
            A C-compatible callback function.
        """

        def wrapped(_user_data: None, entry: typing.Any) -> None:
            """C callback wrapper that copies the entry and calls the Python function."""
            return fn(LogEntry._from_c(entry.contents))

        return k.btck_LogCallback(wrapped)


def _category_logger(
    root: logging.Logger, category: LogCategory | None
) -> logging.Logger:
    """Return the child logger of `root` for `category`, or `root` for NONE."""
    if category is None or category == LogCategory.NONE:
        return root
    return root.getChild(category.name)


class KernelLogViewer:
    """Integration between bitcoinkernel logging and Python's logging module.

    KernelLogViewer bridges bitcoinkernel's logging system with Python's
    standard logging module. It creates a LoggingConnection that converts
    kernel log entries into LogRecords and forwards them to Python loggers.

    Entries are organized by category, with each category getting its own
    child logger. For example, VALIDATION entries go to a logger named
    "bitcoinkernel.VALIDATION". Entries with category NONE go to the root
    logger.

    Note:
        An entry is only forwarded if it passes both the kernel's minimum
        level (set via the `level` parameter) and the level of the Python
        logger for its category.
    """

    def __init__(
        self,
        name: str = "bitcoinkernel",
        level: LogLevel = LogLevel.INFO,
    ):
        """Create a log viewer that forwards kernel logs to Python logging.

        Args:
            name: Name for the root logger. Defaults to "bitcoinkernel".
            level: Minimum kernel log level. This changes a global setting,
                see [logging_set_min_level][pbk.logging_set_min_level].
                Defaults to `LogLevel.INFO`.
        """
        self.name = name
        self._logger = logging.getLogger(name)
        logging_set_min_level(level)
        self.conn = LoggingConnection(cb=self._create_log_callback(self._logger))

    def getLogger(self, category: LogCategory | None = None) -> logging.Logger:
        """Get the Python logger for a specific category.

        Args:
            category: The log category to get a logger for. If None or
                `LogCategory.NONE`, returns the root logger.

        Returns:
            A logging.Logger instance for the specified category.
        """
        return _category_logger(self._logger, category)

    @staticmethod
    def _create_log_callback(root: logging.Logger) -> Callable[[LogEntry], None]:
        """Create a callback that forwards kernel log entries to Python loggers.

        Args:
            root: The root logger. Entries go to its child logger for their
                category.

        Returns:
            A callback function that accepts kernel log entries.
        """

        def callback(entry: LogEntry) -> None:
            """Forward a kernel log entry to the logger for its category."""
            logger = _category_logger(root, entry.category)
            if logger.isEnabledFor(KERNEL_LEVEL_TO_PYTHON[entry.level]):
                logger.handle(make_log_record(logger.name, entry))

        return callback


def make_log_record(logger_name: str, entry: LogEntry) -> logging.LogRecord:
    """Convert a kernel log entry into a Python LogRecord.

    Args:
        logger_name: Name of the logger that handles the record.
        entry: The kernel log entry.

    Returns:
        A LogRecord suitable for handling by Python's logging system.
    """
    path = Path(entry.file_name)
    return logging.makeLogRecord(
        {
            "name": logger_name,
            "levelno": KERNEL_LEVEL_TO_PYTHON[entry.level],
            "levelname": entry.level.name,
            "pathname": entry.file_name,
            "filename": path.name,
            "module": path.stem,
            "lineno": entry.line,
            "msg": entry.message,
            "args": (),
            "exc_info": None,
            "funcName": entry.function_name,
            "created": entry.timestamp_ns / 1e9,
            "msecs": (entry.timestamp_ns // 1_000_000) % 1000,
            "threadName": entry.thread_name,
        }
    )
