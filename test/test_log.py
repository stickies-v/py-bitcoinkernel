import logging

import pbk
import pbk.log


def dummy_fn(entry):
    pass


def test_is_valid_log_callback():
    assert pbk.log.is_valid_log_callback(lambda entry: print(entry.message))
    assert pbk.log.is_valid_log_callback(dummy_fn)

    assert not pbk.log.is_valid_log_callback(lambda: print("hello"))
    assert not pbk.log.is_valid_log_callback(lambda entry, dummy: print(entry))


def test_level_category():
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


def test_kernel_log_viewer(caplog):
    caplog.set_level(logging.DEBUG)
    logger = pbk.KernelLogViewer(name="test_logger", categories=[])
    assert logger.getLogger() == logging.getLogger("test_logger")

    # Test that log entries are correctly forwarded through temporary_categories
    with logger.temporary_categories(categories=[pbk.LogCategory.KERNEL]):
        assert logger.getLogger().getEffectiveLevel() == logging.DEBUG
        try:
            pbk.Block(bytes.fromhex("ab"))
        except RuntimeError:
            pass
        assert caplog.records[-1].message == "Block decode failed."

    # Test KernelLogViewer with categories enabled at construction
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
