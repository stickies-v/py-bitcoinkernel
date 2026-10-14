import pbk.capi.bindings as k


def set_mock_time(timestamp: int) -> None:
    """Override the current time with a fixed timestamp for testing.

    Affects all kernel time reads globally. The caller is responsible for
    gating usage (e.g. restricting to regtest) if desired.

    The upper bound (4294967295) matches the maximum value of a block header
    timestamp.

    Args:
        timestamp: Unix epoch seconds, or 0 to restore the system clock.

    Raises:
        ValueError: If the timestamp is outside the valid [0, 4294967295]
            range.
    """
    if k.btck_set_mock_time(timestamp):
        raise ValueError(f"Mock time {timestamp} is outside [0, 4294967295]")
