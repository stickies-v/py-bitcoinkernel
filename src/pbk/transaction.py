import ctypes
import typing

import pbk.capi.bindings as k
from pbk.capi import KernelOpaquePtr
from pbk.script import ScriptPubkey
from pbk.util.sequence import LazySequence
from pbk.writer import ByteWriter


class Txid(KernelOpaquePtr):
    """Transaction identifier.

    Note:
        Txid instances cannot be directly constructed. They are obtained from
        Transaction objects or TransactionOutPoint objects.
    """

    def __bytes__(self) -> bytes:
        """Serialize the txid to bytes.

        Returns:
            The 32-byte txid in little-endian byte order.
        """
        hash_array = (ctypes.c_ubyte * 32)()
        k.btck_txid_to_bytes(self, hash_array)
        return bytes(hash_array)

    def __eq__(self, other: typing.Any) -> bool:
        """Check equality with another txid.

        Args:
            other: Object to compare with.

        Returns:
            True if both are Txid instances with equal values.
        """
        if not isinstance(other, Txid):
            return False
        return bool(k.btck_txid_equals(self, other))

    def __hash__(self) -> int:
        """Get hash value for use in sets and dictionaries.

        Returns:
            Hash of the txid bytes.
        """
        return hash(bytes(self))

    def __str__(self) -> str:
        """Get the hexadecimal representation of the txid.

        Returns:
            The txid as a 64-character hex string in big-endian
            byte order (standard Bitcoin display format).
        """
        # bytes are serialized in little-endian byte order, typically displayed in big-endian byte order
        return bytes(self)[::-1].hex()

    def __repr__(self) -> str:
        """Return a string representation of the txid."""
        return f"Txid({bytes(self)!r})"


class TransactionOutPoint(KernelOpaquePtr):
    """Reference to a specific output of a transaction.

    A transaction outpoint identifies a specific output by combining a
    transaction ID with an output index. This is used in transaction inputs
    to specify which previous output is being spent.

    Note:
        TransactionOutPoint instances cannot be directly constructed. They are
        obtained from TransactionInput objects.
    """

    @property
    def index(self) -> int:
        """The output index within the transaction.

        Returns:
            The zero-based output position.
        """
        return k.btck_transaction_out_point_get_index(self)

    @property
    def txid(self) -> Txid:
        """The transaction ID being referenced.

        Returns:
            The txid of the transaction containing the output.
        """
        return Txid._from_view(k.btck_transaction_out_point_get_txid(self), self)

    def __repr__(self) -> str:
        """Return a string representation of the transaction outpoint."""
        return f"<TransactionOutPoint txid={str(self.txid)} index={self.index}>"


class TransactionInput(KernelOpaquePtr):
    """Input to a transaction that spends a previous output.

    Note:
        TransactionInput instances cannot be directly constructed. They are
        obtained from Transaction objects.
    """

    @property
    def out_point(self) -> TransactionOutPoint:
        """The outpoint being spent by this input.

        Returns:
            The transaction outpoint referencing the previous output.
        """
        return TransactionOutPoint._from_view(
            k.btck_transaction_input_get_out_point(self), self
        )

    def __repr__(self) -> str:
        """Return a string representation of the transaction input."""
        return f"<TransactionInput {self.out_point!r}>"


class TransactionOutput(KernelOpaquePtr):
    """Output from a transaction that can be spent.

    A transaction output specifies an amount of bitcoin and the conditions
    (script pubkey) required to spend it. Outputs can be created directly
    or obtained from existing transactions.
    """

    _create_fn = k.btck_transaction_output_create
    _destroy_fn = k.btck_transaction_output_destroy

    def __init__(self, script_pubkey: "ScriptPubkey", amount: int):
        """Create a transaction output.

        Args:
            script_pubkey: The script pubkey defining spending conditions.
            amount: The amount in satoshis.
        """
        super().__init__(script_pubkey, amount)

    @property
    def amount(self) -> int:
        """The value of this output in satoshis.

        Returns:
            The amount in satoshis.
        """
        return k.btck_transaction_output_get_amount(self)

    @property
    def script_pubkey(self) -> "ScriptPubkey":
        """The spending conditions for this output.

        Returns:
            The script pubkey defining how this output can be spent.
        """
        ptr = k.btck_transaction_output_get_script_pubkey(self)
        return ScriptPubkey._from_view(ptr, self)

    def __repr__(self) -> str:
        """Return a string representation of the transaction output."""
        return f"<TransactionOutput amount={self.amount} spk_len={len(bytes(self.script_pubkey))}>"


class TransactionInputSequence(LazySequence[TransactionInput]):
    """Lazily-evaluated sequence of transaction inputs.

    This sequence provides indexed access to the inputs of a transaction.
    The sequence is a view into the transaction and caches its length on
    first access.
    """

    def __init__(self, transaction: "Transaction"):
        """Create a sequence view of transaction inputs.

        Args:
            transaction: The transaction to create a sequence view for.
        """
        self._transaction = transaction

    def __len__(self) -> int:
        """Number of inputs in the transaction.

        Returns:
            The input count (cached after first call).
        """
        if not hasattr(self, "_cached_len"):
            self._cached_len = k.btck_transaction_count_inputs(self._transaction)
        return self._cached_len

    def _get_item(self, index: int) -> TransactionInput:
        """Get the transaction input at the given index."""
        return TransactionInput._from_view(
            k.btck_transaction_get_input_at(self._transaction, index), self._transaction
        )


class TransactionOutputSequence(LazySequence[TransactionOutput]):
    """Lazily-evaluated sequence of transaction outputs.

    This sequence provides indexed access to the outputs of a transaction.
    The sequence is a view into the transaction and caches its length on
    first access.
    """

    def __init__(self, transaction: "Transaction"):
        """Create a sequence view of transaction outputs.

        Args:
            transaction: The transaction to create a sequence view for.
        """
        self._transaction = transaction

    def __len__(self) -> int:
        """Number of outputs in the transaction.

        Returns:
            The output count (cached after first call).
        """
        if not hasattr(self, "_cached_len"):
            self._cached_len = k.btck_transaction_count_outputs(self._transaction)
        return self._cached_len

    def _get_item(self, index: int) -> TransactionOutput:
        """Get the transaction output at the given index."""
        return TransactionOutput._from_view(
            k.btck_transaction_get_output_at(self._transaction, index),
            self._transaction,
        )


class Transaction(KernelOpaquePtr):
    """A Bitcoin transaction."""

    _create_fn = k.btck_transaction_create
    _destroy_fn = k.btck_transaction_destroy

    def __init__(self, data: bytes):
        """Create a transaction from serialized data.

        Args:
            data: The serialized transaction data in consensus format.

        Raises:
            RuntimeError: If parsing the transaction data fails (propagated from base class).
        """
        super().__init__((ctypes.c_ubyte * len(data))(*data), len(data))

    def _get_input_at(self, index: int) -> TransactionInput:
        """Get the transaction input at the given index."""
        return TransactionInput._from_view(
            k.btck_transaction_get_input_at(self, index), self
        )

    def _get_output_at(self, index: int) -> TransactionOutput:
        """Get the transaction output at the given index."""
        return TransactionOutput._from_view(
            k.btck_transaction_get_output_at(self, index), self
        )

    @property
    def inputs(self) -> TransactionInputSequence:
        """All inputs of this transaction.

        Returns:
            A lazy sequence of transaction inputs.
        """
        return TransactionInputSequence(self)

    @property
    def outputs(self) -> TransactionOutputSequence:
        """All outputs of this transaction.

        Returns:
            A lazy sequence of transaction outputs.
        """
        return TransactionOutputSequence(self)

    @property
    def txid(self) -> Txid:
        """The transaction identifier.

        Returns:
            The txid of this transaction.
        """
        return Txid._from_view(k.btck_transaction_get_txid(self), self)

    def __bytes__(self) -> bytes:
        """Serialize the transaction to bytes.

        Returns:
            The serialized transaction data in consensus format, suitable
            for P2P network transmission.
        """
        writer = ByteWriter()
        return writer.write(k.btck_transaction_to_bytes, self)

    def __repr__(self) -> str:
        """Return a string representation of the transaction."""
        return f"<Transaction txid={str(self.txid)} ins={len(self.inputs)} outs={len(self.outputs)}>"


class Coin(KernelOpaquePtr):
    """A coin representing a spendable transaction output.

    A coin holds information about a transaction output including the
    output itself, the height at which it was created, and whether it
    came from a coinbase transaction. Coins are typically obtained from
    spent output data.

    Note:
        Coin instances cannot be directly constructed. They are obtained
        from TransactionSpentOutputs objects.
    """

    @property
    def confirmation_height(self) -> int:
        """The block height where this coin was created.

        Returns:
            The height of the block containing the transaction that
            created this coin.
        """
        return k.btck_coin_confirmation_height(self)

    @property
    def is_coinbase(self) -> bool:
        """Whether this coin came from a coinbase transaction.

        Returns:
            True if the transaction that created this coin was a coinbase
            transaction, False otherwise.
        """
        res = k.btck_coin_is_coinbase(self)
        assert res in [0, 1]
        return bool(res)

    @property
    def output(self) -> TransactionOutput:
        """The transaction output for this coin.

        Returns:
            The transaction output containing the amount and script pubkey.
        """
        ptr = k.btck_coin_get_output(self)
        return TransactionOutput._from_view(ptr, self)

    def __repr__(self) -> str:
        """Return a string representation of the coin."""
        return f"<Coin height={self.confirmation_height} amount={self.output.amount} coinbase={self.is_coinbase}>"


class CoinSequence(LazySequence[Coin]):
    """Lazily-evaluated sequence of coins spent by a transaction.

    This sequence provides indexed access to the coins (previous outputs)
    consumed by a transaction's inputs. The sequence is a view and caches
    its length on first access.
    """

    def __init__(self, spent_outputs: "TransactionSpentOutputs"):
        """Create a sequence view of coins.

        Args:
            spent_outputs: The transaction spent outputs to create a sequence view for.
        """
        self._spent_outputs = spent_outputs

    def __len__(self) -> int:
        """Number of coins spent by the transaction.

        Returns:
            The coin count, equal to the number of inputs (cached after first call).
        """
        if not hasattr(self, "_cached_len"):
            self._cached_len = k.btck_transaction_spent_outputs_count(
                self._spent_outputs
            )
        return self._cached_len

    def _get_item(self, index: int) -> Coin:
        """Get the coin at the given index."""
        ptr = k.btck_transaction_spent_outputs_get_coin_at(self._spent_outputs, index)
        return Coin._from_view(ptr, self._spent_outputs)


class TransactionSpentOutputs(KernelOpaquePtr):
    """Coins consumed by a transaction's inputs.

    This holds the previous outputs (coins) consumed by a transaction.
    Each coin corresponds to one of the transaction's inputs, in the same
    order. This data is part of the block's undo data and is necessary
    for validation and chain reorganizations.

    Note:
        TransactionSpentOutputs instances cannot be directly constructed.
        They are obtained from BlockSpentOutputs objects.
    """

    def _get_coin_at(self, index: int) -> Coin:
        """Get the coin at the given index."""
        ptr = k.btck_transaction_spent_outputs_get_coin_at(self, index)
        return Coin._from_view(ptr, self)

    @property
    def coins(self) -> CoinSequence:
        """All coins spent by this transaction.

        Returns:
            A sequence of coins, one for each input, in input order.
        """
        return CoinSequence(self)

    def __repr__(self) -> str:
        """Return a string representation of the transaction spent outputs."""
        return f"<TransactionSpentOutputs coins={len(self.coins)}>"
