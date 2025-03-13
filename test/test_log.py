import pbk.log


def dummy_fn(msg):
    pass


def test_is_valid_log_callback():
    assert pbk.log.is_valid_log_callback(lambda msg: print(msg))
    assert pbk.log.is_valid_log_callback(dummy_fn)

    assert not pbk.log.is_valid_log_callback(lambda: print("hello"))
    assert not pbk.log.is_valid_log_callback(lambda msg, dummy: print(msg))
