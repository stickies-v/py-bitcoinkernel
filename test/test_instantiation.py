"""Test that non-instantiable classes raise TypeError consistently."""

import pytest
import pbk


def test_non_instantiable_classes_raise_type_error():
    """Non-instantiable classes should raise TypeError with a clear message."""
    # Only test publicly exported types
    non_instantiable_classes = [
        (pbk.BlockIndex, "BlockIndex"),
        (pbk.BlockSpentOutputs, "BlockSpentOutputs"),
        (pbk.Chain, "Chain"),
        (pbk.Coin, "Coin"),
        (pbk.Txid, "Txid"),
        (pbk.TransactionOutPoint, "TransactionOutPoint"),
        (pbk.TransactionInput, "TransactionInput"),
        (pbk.TransactionSpentOutputs, "TransactionSpentOutputs"),
        (pbk.BlockValidationState, "BlockValidationState"),
    ]

    for cls, name in non_instantiable_classes:
        with pytest.raises(
            TypeError,
            match=f"{name} cannot be instantiated directly.",
        ):
            cls()


def test_instantiable_classes_work():
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
