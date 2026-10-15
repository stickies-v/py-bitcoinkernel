import ctypes
import logging
import time

import pytest

import pbk
import pbk.capi.bindings as k
import pbk.log
from pbk.log import LogCategory, LogLevel


def _trigger_kernel_debug_log() -> None:
    """Make the kernel log the DEBUG entry "Block decode failed."."""
    with pytest.raises(RuntimeError):
        pbk.Block(bytes.fromhex("ab"))


def _decode_failed_records(
    caplog: pytest.LogCaptureFixture,
) -> list[logging.LogRecord]:
    return [r for r in caplog.records if r.getMessage() == "Block decode failed."]


def test_python_logging(caplog: pytest.LogCaptureFixture) -> None:
    assert any(
        isinstance(handler, logging.NullHandler)
        for handler in logging.getLogger("btck").handlers
    )

    caplog.set_level(logging.DEBUG, logger="btck.KERNEL")
    assert pbk.log._bridge.kernel_level == LogLevel.DEBUG

    before_ns = time.time_ns()
    _trigger_kernel_debug_log()
    after_ns = time.time_ns()
    [record] = _decode_failed_records(caplog)
    assert record.name == "btck.KERNEL"
    assert record.levelno == logging.DEBUG
    assert record.levelname == "DEBUG"
    assert record.filename == "bitcoinkernel.cpp"
    assert record.funcName == "btck_block_create"
    assert record.lineno > 0
    assert record.threadName == "MainThread"  # the kernel did not name this thread
    assert before_ns <= vars(record)["btck_timestamp_ns"] <= after_ns
    assert record.created == pytest.approx(vars(record)["btck_timestamp_ns"] / 1e9)
    assert vars(record)["btck_category"] == "KERNEL"
    assert vars(record)["btck_mocktime_s"] == 0

    formatter = logging.Formatter("[%(btck_category)s] %(message)s")
    assert formatter.format(record) == "[KERNEL] Block decode failed."


def test_python_logging_filters_per_category(caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.INFO, logger="btck")
    caplog.set_level(logging.DEBUG, logger="btck.VALIDATION")
    caplog.set_level(logging.DEBUG)  # let caplog's handler capture DEBUG records
    assert pbk.log._bridge.kernel_level == LogLevel.DEBUG

    # The kernel produces the KERNEL entry, but the btck.KERNEL logger drops it.
    _trigger_kernel_debug_log()
    assert _decode_failed_records(caplog) == []

    caplog.set_level(logging.DEBUG, logger="btck.KERNEL")
    _trigger_kernel_debug_log()
    assert len(_decode_failed_records(caplog)) == 1


def test_kernel_level_follows_python_levels() -> None:
    root = logging.getLogger("btck")
    validation = logging.getLogger("btck.VALIDATION")
    saved_levels = root.level, validation.level

    def kernel_level_for(root_level: int, validation_level: int) -> LogLevel:
        root.setLevel(root_level)
        validation.setLevel(validation_level)
        level = pbk.log._bridge.kernel_level
        assert level is not None
        return level

    try:
        expected = [
            ((logging.WARNING, logging.NOTSET), LogLevel.WARNING),
            ((logging.WARNING, logging.DEBUG), LogLevel.DEBUG),
            ((logging.WARNING, logging.DEBUG - 5), LogLevel.TRACE),
            ((logging.DEBUG + 5, logging.NOTSET), LogLevel.INFO),
            ((logging.ERROR, logging.NOTSET), LogLevel.ERROR),
            # The kernel has no level above ERROR; Python drops the entries.
            ((logging.CRITICAL, logging.NOTSET), LogLevel.ERROR),
        ]
        for levels, kernel_level in expected:
            assert kernel_level_for(*levels) == kernel_level

        root.setLevel(logging.DEBUG)
        logging.disable(logging.INFO)
        assert pbk.log._bridge.kernel_level == LogLevel.WARNING
    finally:
        logging.disable(logging.NOTSET)
        root.setLevel(saved_levels[0])
        validation.setLevel(saved_levels[1])


def _c_log_entry(message: str, level: LogLevel) -> tuple[k.btck_LogEntry, list]:
    """Build a C log entry. The returned list keeps its buffers alive."""
    fields = {
        "message": message,
        "thread_name": "b-scriptch.0",
        "file_name": "depend/bitcoin/src/kernel/context.cpp",
        "function_name": "operator()",
    }
    buffers = []
    entry = k.btck_LogEntry()
    for name, value in fields.items():
        data = value.encode()
        buffer = ctypes.create_string_buffer(data, len(data))
        buffers.append(buffer)
        setattr(entry, name, ctypes.cast(buffer, ctypes.POINTER(ctypes.c_char)))
        setattr(entry, f"{name}_len", len(data))
    entry.timestamp_ns = 1_742_386_495_123_456_789
    entry.mocktime_s = 1_700_000_000
    entry.line = 20
    entry.level = level
    entry.category = LogCategory.VALIDATION
    return entry, buffers


def test_make_log_record() -> None:
    entry, _buffers = _c_log_entry("Connected block\n", LogLevel.TRACE)
    record = pbk.log._make_log_record("btck.VALIDATION", entry)
    assert record.name == "btck.VALIDATION"
    assert record.levelno == logging.DEBUG - 5
    assert record.levelname == "TRACE"
    assert record.filename == "context.cpp"
    assert record.module == "context"
    assert record.pathname == "depend/bitcoin/src/kernel/context.cpp"
    assert record.lineno == 20
    assert record.threadName == "b-scriptch.0"
    assert record.funcName == "operator()"
    assert record.created == pytest.approx(1_742_386_495.123456789)
    assert record.msecs == 123
    assert vars(record)["btck_category"] == "VALIDATION"
    assert vars(record)["btck_timestamp_ns"] == 1_742_386_495_123_456_789
    assert vars(record)["btck_mocktime_s"] == 1_700_000_000
    assert record.getMessage() == "Connected block\\n"


def test_make_log_record_escapes_message() -> None:
    raw = "a\nb\rc\td\x00e\x1bf\x7fg\x85h i j é ✓"
    entry, _buffers = _c_log_entry(raw, LogLevel.INFO)
    message = pbk.log._make_log_record("btck", entry).getMessage()
    assert message == "a\\nb\\rc\\td\\x00e\\x1bf\\x7fg\\x85h\\u2028i\\u2029j é ✓"
    assert message.isprintable()
    assert len(message.splitlines()) == 1
