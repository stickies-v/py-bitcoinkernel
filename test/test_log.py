import pbk.log


def dummy_fn(msg):
    pass


def test_is_valid_log_callback():
    assert pbk.log.is_valid_log_callback(lambda msg: print(msg))
    assert pbk.log.is_valid_log_callback(dummy_fn)

    assert not pbk.log.is_valid_log_callback(lambda: print("hello"))
    assert not pbk.log.is_valid_log_callback(lambda msg, dummy: print(msg))


def test_level_category():
    assert pbk.add_log_level_category(pbk.LogCategory.ALL, pbk.LogLevel.TRACE)
    assert pbk.add_log_level_category(pbk.LogCategory.ALL, pbk.LogLevel.DEBUG)
    assert pbk.add_log_level_category(pbk.LogCategory.ALL, pbk.LogLevel.INFO)
    assert pbk.add_log_level_category(
        pbk.LogCategory.ALL, pbk.LogLevel.INFO
    )  # Same operation twice should succeed

    assert pbk.add_log_level_category(pbk.LogCategory.BLOCKSTORAGE, pbk.LogLevel.DEBUG)

    assert pbk.enable_log_category(pbk.LogCategory.BLOCKSTORAGE)
    assert pbk.enable_log_category(
        pbk.LogCategory.BLOCKSTORAGE
    )  # Same operation twice should succeed
    assert pbk.disable_log_category(pbk.LogCategory.BLOCKSTORAGE)
    assert pbk.disable_log_category(
        pbk.LogCategory.BLOCKSTORAGE
    )  # Same operation twice should succeed

    # # Operations should fail when unknown flags are passed
    # TODO: this currently crashes because an assertion in log_{category,level}_to_string in bitcoinkernel.cpp
    # assert not pbk.add_log_level_category(max(pbk.LogCategory) + 1, pbk.LogLevel.INFO)
    # assert not pbk.add_log_level_category(pbk.LogCategory.KERNEL, max(pbk.LogLevel) + 1)
    # assert not pbk.add_log_level_category(max(pbk.LogCategory) + 1, max(pbk.LogLevel) + 1)
    # assert not pbk.enable_log_category(max(pbk.LogCategory) + 1)
    # assert not pbk.disable_log_category(max(pbk.LogCategory) + 1)
