import pytest

import pbk


def test_validation_state() -> None:
    state = pbk.BlockValidationState()
    assert state.block_validation_result == pbk.BlockValidationResult.UNSET
    assert state.validation_mode == pbk.ValidationMode.VALID


def _noop(*_args: object) -> None:
    pass


VALIDATION_CALLBACK_NAMES = (
    "block_checked",
    "pow_valid_block",
    "block_connected",
    "block_disconnected",
)


def test_validation_callbacks_single() -> None:
    cb = pbk.ValidationInterfaceCallbacks(block_disconnected=_noop)
    assert bool(cb.block_disconnected)
    for name in set(VALIDATION_CALLBACK_NAMES) - {"block_disconnected"}:
        assert not bool(getattr(cb, name))


def test_validation_callbacks_empty() -> None:
    cb = pbk.ValidationInterfaceCallbacks()
    for name in VALIDATION_CALLBACK_NAMES:
        assert not bool(getattr(cb, name))


def test_validation_callbacks_all() -> None:
    cb = pbk.ValidationInterfaceCallbacks(
        block_checked=_noop,
        pow_valid_block=_noop,
        block_connected=_noop,
        block_disconnected=_noop,
    )
    for name in VALIDATION_CALLBACK_NAMES:
        assert bool(getattr(cb, name))


def test_validation_callbacks_unknown_raises() -> None:
    with pytest.raises(ValueError, match="not recognized"):
        pbk.ValidationInterfaceCallbacks(block_disconected=_noop)


def test_validation_callbacks_reserved_names_rejected() -> None:
    # `user_data` is a declared parameter, not a callback. `user_data_destroy`
    # is a struct field reserved for internal use and must not be settable
    # via the callback kwargs.
    with pytest.raises(ValueError, match="not recognized"):
        pbk.ValidationInterfaceCallbacks(user_data_destroy=_noop)
