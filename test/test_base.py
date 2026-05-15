"""Tests for `KernelOpaquePtr` base-class behaviour."""

from collections.abc import Callable

import pbk
import pytest
from pbk.capi import KernelOpaquePtr


def test_non_instantiable_classes_raise_type_error() -> None:
    """Non-instantiable classes should raise TypeError with a clear message."""
    # Only test publicly exported types
    non_instantiable_classes = [
        (pbk.BlockTreeEntry, "BlockTreeEntry"),
        (pbk.BlockSpentOutputs, "BlockSpentOutputs"),
        (pbk.Chain, "Chain"),
        (pbk.Coin, "Coin"),
        (pbk.Txid, "Txid"),
        (pbk.TransactionOutPoint, "TransactionOutPoint"),
        (pbk.TransactionInput, "TransactionInput"),
        (pbk.TransactionSpentOutputs, "TransactionSpentOutputs"),
    ]

    for cls, name in non_instantiable_classes:
        with pytest.raises(
            TypeError,
            match=f"{name} cannot be instantiated directly.",
        ):
            cls()


def test_instantiable_classes_work() -> None:
    """Instantiable classes should not raise TypeError when instantiated."""
    # Test just that they don't raise TypeError - we don't need to keep the objects
    # Some may fail for other reasons (invalid data), but that's okay for this test

    # These should succeed
    pbk.BlockHash(b"0" * 32)
    pbk.ScriptPubkey(b"\x00")
    pbk.TransactionOutput(pbk.ScriptPubkey(b"\x00"), 100)
    pbk.ChainParameters(pbk.ChainType.REGTEST)
    pbk.ContextOptions()

    # Block and Transaction might fail with RuntimeError due to invalid data,
    # but should NOT raise TypeError about instantiation
    try:
        pbk.Block(b"\x01" * 100)
    except RuntimeError:
        pass  # Expected - invalid block data
    except TypeError as e:
        if "cannot be instantiated directly" in str(e):
            raise  # This shouldn't happen!

    try:
        pbk.Transaction(b"\x01" * 10)
    except RuntimeError:
        pass  # Expected - invalid transaction data
    except TypeError as e:
        if "cannot be instantiated directly" in str(e):
            raise  # This shouldn't happen!


# Factories that produce an owned instance of each directly-constructible
# kernel type. Used to verify base-class behaviour (e.g. `detach()` is a
# no-op on owned handles) across the type hierarchy without hand-writing one
# test per class.
_OWNED_FACTORIES = {
    "BlockHash": lambda: pbk.BlockHash(b"0" * 32),
    "ScriptPubkey": lambda: pbk.ScriptPubkey(b"\x00"),
    "TransactionOutput": lambda: pbk.TransactionOutput(pbk.ScriptPubkey(b"\x00"), 1),
    "ChainParameters": lambda: pbk.ChainParameters(pbk.ChainType.REGTEST),
}


@pytest.mark.parametrize(
    "factory", _OWNED_FACTORIES.values(), ids=_OWNED_FACTORIES.keys()
)
def test_detach_is_noop_on_owned_handle(factory: Callable[[], KernelOpaquePtr]) -> None:
    obj = factory()
    ptr_before = obj._as_parameter_

    assert obj.detach() is obj
    assert obj._owns_ptr is True
    assert obj._as_parameter_ is ptr_before


def test_detach_raises_on_noncopyable_view(
    chainman_regtest: pbk.ChainstateManager,
) -> None:
    # BlockTreeEntry is a view-only type whose C API exposes no copy
    # function. Calling detach() on such a view must raise rather than
    # silently leave the user with a still-borrowed handle.
    entry = chainman_regtest.get_active_chain().block_tree_entries[0]

    assert entry._copy_fn is None

    with pytest.raises(TypeError, match="cannot be copied"):
        entry.detach()
