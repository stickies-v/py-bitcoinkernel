from pathlib import Path

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


def test_validation_callbacks_wrap_block_and_entry(temp_dir: Path) -> None:
    received: list[tuple[pbk.Block, pbk.BlockTreeEntry]] = []
    cm = pbk.load_chainman(
        temp_dir,
        pbk.ChainType.REGTEST,
        pbk.ValidationInterfaceCallbacks(
            block_connected=lambda u, b, e: received.append((b, e)),
        ),
    )
    with (Path(__file__).parent / "data" / "regtest" / "blocks.txt").open() as f:
        block = pbk.Block(bytes.fromhex(f.readline().strip()))
    assert cm.process_block(block)
    assert received
    for block_arg, entry_arg in received:
        assert isinstance(block_arg, pbk.Block)
        assert isinstance(entry_arg, pbk.BlockTreeEntry)
        # Both should be usable — exercise a property on each.
        assert isinstance(entry_arg.height, int)
        assert isinstance(block_arg.block_hash, pbk.BlockHash)


def test_validation_callbacks_wrap_block_and_state(temp_dir: Path) -> None:
    received: list[tuple[str, str, pbk.ValidationMode]] = []

    def on_checked(
        user_data: object, block: pbk.Block, state: pbk.BlockValidationState
    ) -> None:
        # `state` is only valid inside the callback — read it here.
        received.append(
            (type(block).__name__, type(state).__name__, state.validation_mode)
        )

    cm = pbk.load_chainman(
        temp_dir,
        pbk.ChainType.REGTEST,
        pbk.ValidationInterfaceCallbacks(block_checked=on_checked),
    )
    with (Path(__file__).parent / "data" / "regtest" / "blocks.txt").open() as f:
        block = pbk.Block(bytes.fromhex(f.readline().strip()))
    assert cm.process_block(block)
    assert received
    for block_type, state_type, mode in received:
        assert block_type == "Block"
        assert state_type == "BlockValidationState"
        assert mode == pbk.ValidationMode.VALID
