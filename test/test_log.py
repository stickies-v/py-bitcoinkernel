import pbk.log


def dummy_fn(msg):
    pass


def test_is_valid_log_callback():
    assert pbk.log.is_valid_log_callback(lambda msg: print(msg))
    assert pbk.log.is_valid_log_callback(dummy_fn)

    assert not pbk.log.is_valid_log_callback(lambda: print("hello"))
    assert not pbk.log.is_valid_log_callback(lambda msg, dummy: print(msg))


def test_level_category():
    pbk.add_log_level_category(pbk.LogCategory.ALL, pbk.LogLevel.DEBUG)
    pbk.add_log_level_category(pbk.LogCategory.ALL, pbk.LogLevel.INFO)
    pbk.add_log_level_category(
        pbk.LogCategory.ALL, pbk.LogLevel.INFO
    )  # Same operation twice should succeed

    pbk.add_log_level_category(pbk.LogCategory.BLOCKSTORAGE, pbk.LogLevel.DEBUG)

    pbk.enable_log_category(pbk.LogCategory.BLOCKSTORAGE)
    pbk.enable_log_category(
        pbk.LogCategory.BLOCKSTORAGE
    )  # Same operation twice should succeed
    pbk.disable_log_category(pbk.LogCategory.BLOCKSTORAGE)
    pbk.disable_log_category(
        pbk.LogCategory.BLOCKSTORAGE
    )  # Same operation twice should succeed
