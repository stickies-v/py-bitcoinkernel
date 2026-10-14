import atexit
import ctypes
import logging
import threading
import typing
import warnings
from enum import IntEnum
from pathlib import Path

import pbk.capi.bindings as k
from pbk.capi import KernelOpaquePtr

LOGGER_NAME = "btck"
"""Name of the Python logger that receives kernel log entries."""


# TODO: add enum auto-generation or testing to ensure it remains in
# sync with bitcoinkernel.h
class LogCategory(IntEnum):
    """A collection of logging categories that may be encountered by kernel code.

    Entries go to the `btck.<NAME>` logger of their category. Entries with
    category NONE go to the `btck` logger.
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
    """The severity of a log statement."""

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

# Control characters and the characters that str.splitlines() treats as line
# breaks, so that every message is printable and fits on one line.
_ESCAPES = {
    **{c: f"\\x{c:02x}" for c in [*range(0x20), *range(0x7F, 0xA0)]},
    ord("\n"): "\\n",
    ord("\r"): "\\r",
    ord("\t"): "\\t",
    0x2028: "\\u2028",
    0x2029: "\\u2029",
}


def _escape(message: str) -> str:
    """Escape control characters and line breaks in a log message."""
    return message.translate(_ESCAPES)


def _decode(ptr: typing.Any, length: int) -> str:
    """Copy a non-null-terminated C string into a Python string."""
    return ctypes.string_at(ptr, length).decode("utf-8", errors="replace")


def _make_log_record(logger_name: str, entry: k.btck_LogEntry) -> logging.LogRecord:
    """Convert a kernel log entry into a Python LogRecord.

    Args:
        logger_name: Name of the logger that handles the record.
        entry: The kernel log entry. Only valid during the logging callback.

    Returns:
        A LogRecord suitable for handling by Python's logging system.
    """
    level = LogLevel(entry.level)
    file_name = _decode(entry.file_name, entry.file_name_len)
    path = Path(file_name)
    record = logging.makeLogRecord(
        {
            "name": logger_name,
            "levelno": KERNEL_LEVEL_TO_PYTHON[level],
            "levelname": level.name,
            "pathname": file_name,
            "filename": path.name,
            "module": path.stem,
            "lineno": entry.line,
            "msg": _escape(_decode(entry.message, entry.message_len)),
            "args": (),
            "exc_info": None,
            "funcName": _decode(entry.function_name, entry.function_name_len),
            "created": entry.timestamp_ns / 1e9,
            "msecs": (entry.timestamp_ns // 1_000_000) % 1000,
            "btck_category": LogCategory(entry.category).name,
            "btck_timestamp_ns": entry.timestamp_ns,
            "btck_mocktime_s": entry.mocktime_s,
        }
    )
    # The kernel only names the threads that it starts. On other threads, the
    # Python thread name that makeLogRecord() sets is the useful one.
    if thread_name := _decode(entry.thread_name, entry.thread_name_len):
        record.threadName = thread_name
    return record


def _kernel_level(python_level: int) -> LogLevel:
    """Return the lowest kernel level that a Python logger at `python_level` handles."""
    for level in LogLevel:
        if KERNEL_LEVEL_TO_PYTHON[level] >= python_level:
            return level
    return LogLevel.ERROR


class _LoggingConnection(KernelOpaquePtr):
    """Owned btck_LoggingConnection handle."""

    _destroy_fn = k.btck_logging_connection_destroy


class _PythonLoggingBridge:
    """Forwards kernel log entries to the `btck` Python loggers.

    The kernel only filters on one global minimum level. To prevent entries
    that no Python logger handles from reaching Python, the bridge keeps that
    level at the lowest level that any `btck` logger is enabled for. Python
    has no public hook for level changes, so the bridge wraps
    `Manager._clear_cache()`, which every level change calls to invalidate
    the `isEnabledFor()` cache.
    """

    def __init__(self):
        """Connect to the kernel and start to follow the Python levels."""
        root = logging.getLogger(LOGGER_NAME)
        root.addHandler(logging.NullHandler())
        self._loggers = {
            category: root
            if category == LogCategory.NONE
            else root.getChild(category.name)
            for category in LogCategory
        }
        self._lock = threading.Lock()
        self.kernel_level: LogLevel | None = None
        if self._install_level_hook():
            self.sync_kernel_level()
        else:
            warnings.warn(
                "Cannot follow Python logging level changes, so all kernel log "
                "entries are passed to Python. This can slow down validation.",
                RuntimeWarning,
                stacklevel=2,
            )
            self._set_kernel_level(LogLevel.TRACE)
        self._cb = k.btck_LogCallback(self._forward)  # ensure lifetime
        self._connection: _LoggingConnection | None = _LoggingConnection._from_handle(
            k.btck_logging_connection_create(
                self._cb, ctypes.c_void_p(), k.btck_DestroyCallback()
            )
        )

    def _install_level_hook(self) -> bool:
        """Sync the kernel level after each Python level change.

        Returns:
            False if the Python logging internals are not as expected.
        """
        manager = logging.Logger.manager
        clear_cache = getattr(manager, "_clear_cache", None)
        if not callable(clear_cache):
            return False

        def clear_cache_and_sync() -> None:
            """Clear the Python logging cache, then sync the kernel level."""
            clear_cache()
            self.sync_kernel_level()

        manager._clear_cache = clear_cache_and_sync  # ty: ignore[unresolved-attribute]
        return True

    def _set_kernel_level(self, level: LogLevel) -> None:
        """Set and remember the kernel minimum level."""
        with self._lock:
            self.kernel_level = level
            k.btck_logging_set_min_level(level)

    def sync_kernel_level(self) -> None:
        """Set the kernel level to the lowest level that a `btck` logger handles."""
        lowest = min(logger.getEffectiveLevel() for logger in self._loggers.values())
        disabled_up_to = logging.Logger.manager.disable
        self._set_kernel_level(_kernel_level(max(lowest, disabled_up_to + 1)))

    def _forward(self, _user_data: None, entry_ptr: typing.Any) -> None:
        """C callback that forwards an entry to the logger of its category.

        Entries that the logger does not handle are dropped before they are
        decoded, because that is most of the cost.
        """
        entry = entry_ptr.contents
        logger = self._loggers[entry.category]
        if logger.isEnabledFor(KERNEL_LEVEL_TO_PYTHON[entry.level]):
            logger.handle(_make_log_record(logger.name, entry))

    def close(self) -> None:
        """Disconnect from the kernel, so kernel threads stop calling into Python."""
        self._connection = None


_bridge = _PythonLoggingBridge()
atexit.register(_bridge.close)
