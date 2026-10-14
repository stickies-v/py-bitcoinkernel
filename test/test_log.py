import logging
import time

import pytest

import pbk
import pbk.log


def dummy_fn(entry: pbk.LogEntry) -> None:
    pass


def _trigger_kernel_debug_log() -> None:
    """Make the kernel log the DEBUG entry "Block decode failed."."""
    with pytest.raises(RuntimeError):
        pbk.Block(bytes.fromhex("ab"))


def _find_entry(entries: list[pbk.LogEntry], message: str) -> pbk.LogEntry | None:
    return next((entry for entry in entries if entry.message == message), None)


def test_is_valid_log_callback() -> None:
    assert pbk.log.is_valid_log_callback(lambda entry: print(entry))
    assert pbk.log.is_valid_log_callback(dummy_fn)

    assert not pbk.log.is_valid_log_callback(lambda: print("hello"))
    assert not pbk.log.is_valid_log_callback(lambda entry, dummy: print(entry))


def test_logging_connection() -> None:
    entries: list[pbk.LogEntry] = []
    conn = pbk.LoggingConnection(entries.append)
    try:
        pbk.logging_set_min_level(pbk.LogLevel.DEBUG)
        before_ns = time.time_ns()
        _trigger_kernel_debug_log()
        after_ns = time.time_ns()
    finally:
        pbk.logging_set_min_level(pbk.LogLevel.INFO)

    entry = _find_entry(entries, "Block decode failed.")
    assert entry is not None
    assert entry.level == pbk.LogLevel.DEBUG
    assert entry.category == pbk.LogCategory.KERNEL
    assert entry.file_name.endswith("bitcoinkernel.cpp")
    assert entry.function_name == "btck_block_create"
    assert entry.line > 0
    assert isinstance(entry.thread_name, str)
    assert before_ns <= entry.timestamp_ns <= after_ns
    assert entry.mocktime_s == 0

    # Entries below the minimum level are not delivered.
    entries.clear()
    _trigger_kernel_debug_log()
    assert _find_entry(entries, "Block decode failed.") is None

    # Entries are not delivered after the connection is destroyed.
    del conn
    pbk.logging_set_min_level(pbk.LogLevel.DEBUG)
    try:
        _trigger_kernel_debug_log()
    finally:
        pbk.logging_set_min_level(pbk.LogLevel.INFO)
    assert _find_entry(entries, "Block decode failed.") is None


def test_make_log_record() -> None:
    entry = pbk.LogEntry(
        message="Using the 'arm_shani(1way,2way)' SHA256 implementation",
        thread_name="unknown",
        timestamp_ns=1_742_386_495_123_456_789,
        mocktime_s=0,
        file_name="depend/bitcoin/src/kernel/context.cpp",
        function_name="operator()",
        line=20,
        level=pbk.LogLevel.TRACE,
        category=pbk.LogCategory.KERNEL,
    )
    record = pbk.log.make_log_record("test_logger.KERNEL", entry)
    assert record.name == "test_logger.KERNEL"
    assert record.levelno == logging.DEBUG - 5
    assert record.levelname == "TRACE"
    assert record.filename == "context.cpp"
    assert record.module == "context"
    assert record.pathname == entry.file_name
    assert record.lineno == entry.line
    assert record.getMessage() == entry.message
    assert record.threadName == entry.thread_name
    assert record.funcName == entry.function_name
    assert record.created == pytest.approx(1_742_386_495.123456789)
    assert record.msecs == 123


def test_kernel_log_viewer(caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.DEBUG)
    try:
        viewer = pbk.KernelLogViewer(name="test_logger", level=pbk.LogLevel.DEBUG)
        assert viewer.getLogger() == logging.getLogger("test_logger")
        assert viewer.getLogger(pbk.LogCategory.NONE) == logging.getLogger(
            "test_logger"
        )
        kernel_logger = viewer.getLogger(pbk.LogCategory.KERNEL)
        assert kernel_logger == logging.getLogger("test_logger.KERNEL")

        caplog.clear()
        _trigger_kernel_debug_log()
        record = caplog.records[-1]
        assert record.getMessage() == "Block decode failed."
        assert record.name == "test_logger.KERNEL"
        assert record.levelno == logging.DEBUG
        assert record.levelname == "DEBUG"
        assert record.filename == "bitcoinkernel.cpp"
        assert record.funcName == "btck_block_create"

        # The Python logger level of a category filters its entries.
        kernel_logger.setLevel(logging.INFO)
        try:
            caplog.clear()
            _trigger_kernel_debug_log()
            assert all(r.name != "test_logger.KERNEL" for r in caplog.records)
        finally:
            kernel_logger.setLevel(logging.NOTSET)
    finally:
        pbk.logging_set_min_level(pbk.LogLevel.INFO)
