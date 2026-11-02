import logging
import typing
from datetime import datetime, timezone

import pytest

import pbk
import pbk.log


def dummy_fn(msg: str) -> None:
    pass


def test_is_valid_log_callback() -> None:
    assert pbk.log.is_valid_log_callback(lambda msg: print(msg))
    assert pbk.log.is_valid_log_callback(dummy_fn)

    assert not pbk.log.is_valid_log_callback(lambda: print("hello"))
    assert not pbk.log.is_valid_log_callback(lambda msg, dummy: print(msg))


def test_level_category() -> None:
    pbk.set_log_level_category(pbk.LogCategory.ALL, pbk.LogLevel.DEBUG)
    pbk.set_log_level_category(pbk.LogCategory.ALL, pbk.LogLevel.INFO)
    pbk.set_log_level_category(
        pbk.LogCategory.ALL, pbk.LogLevel.INFO
    )  # Same operation twice should succeed

    pbk.set_log_level_category(pbk.LogCategory.BLOCKSTORAGE, pbk.LogLevel.DEBUG)

    pbk.enable_log_category(pbk.LogCategory.BLOCKSTORAGE)
    pbk.enable_log_category(
        pbk.LogCategory.BLOCKSTORAGE
    )  # Same operation twice should succeed
    pbk.disable_log_category(pbk.LogCategory.BLOCKSTORAGE)
    pbk.disable_log_category(
        pbk.LogCategory.BLOCKSTORAGE
    )  # Same operation twice should succeed

    unknown_category = typing.cast(pbk.LogCategory, len(pbk.LogCategory))
    unknown_level = typing.cast(pbk.LogLevel, max(pbk.LogLevel) + 1)
    with pytest.raises(ValueError, match="not a valid LogCategory"):
        pbk.set_log_level_category(unknown_category, pbk.LogLevel.INFO)
    with pytest.raises(ValueError, match="not a valid LogLevel"):
        pbk.set_log_level_category(pbk.LogCategory.ALL, unknown_level)
    with pytest.raises(ValueError, match="not a valid LogCategory"):
        pbk.enable_log_category(unknown_category)
    with pytest.raises(ValueError, match="not a valid LogCategory"):
        pbk.disable_log_category(unknown_category)


def test_kernel_log_viewer(caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.DEBUG)
    logger = pbk.KernelLogViewer(name="test_logger", categories=[])
    assert logger.getLogger() == logging.getLogger("test_logger")

    time = "2025-03-19T12:14:55Z"
    thread = "unknown"
    filename = "context.cpp"
    path = f"depend/bitcoin/src/kernel/{filename}"
    lineno = 20
    func = "operator()"
    category = "all"
    level = "info"
    msg = "Using the 'arm_shani(1way,2way)' SHA256 implementation"
    log_string = (
        f"{time} [{thread}] [{path}:{lineno}] [{func}] [{category}:{level}] {msg}"
    )
    record = pbk.log.parse_btck_log_string(logger.name, log_string)
    assert record.name == logger.name
    assert record.levelno == logging.INFO
    assert record.levelname == level.upper()
    assert record.filename == filename
    assert record.pathname == path
    assert record.lineno == lineno
    assert record.msg == msg
    assert record.threadName == thread
    assert record.funcName == func
    assert (
        record.created
        == datetime.strptime(time, "%Y-%m-%dT%H:%M:%SZ")
        .replace(tzinfo=timezone.utc)
        .timestamp()
    )

    with logger.temporary_categories(categories=[pbk.LogCategory.KERNEL]):
        assert logger.getLogger().getEffectiveLevel() == logging.DEBUG
        try:
            pbk.Block(bytes.fromhex("ab"))
        except RuntimeError:
            pass
        assert caplog.records[-1].message == "Block decode failed."

    debug_logger = pbk.KernelLogViewer(
        name="debug_logger", categories=[pbk.LogCategory.KERNEL, pbk.LogCategory.PRUNE]
    )
    caplog.clear()
    assert debug_logger.getLogger().getEffectiveLevel() == logging.DEBUG
    try:
        pbk.Block(bytes.fromhex("ab"))
    except RuntimeError:
        pass
    assert caplog.records[-1].message == "Block decode failed."
