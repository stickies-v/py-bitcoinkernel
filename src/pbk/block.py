import ctypes

import pbk.capi.bindings as k
from pbk.capi import KernelOpaquePtr
from pbk.transaction import Transaction, TransactionSpentOutputs
from pbk.util.sequence import LazySequence
from pbk.writer import ByteWriter


class BlockHash(KernelOpaquePtr):
    """Identifier for a block."""

    _create_fn = k.btck_block_hash_create
    _destroy_fn = k.btck_block_hash_destroy

    def __init__(self, block_hash: bytes):
        """Create a block hash from raw bytes.

        Args:
            block_hash: The 32-byte block hash in little-endian byte order.

        Raises:
            ValueError: If the block hash is not exactly 32 bytes.
            RuntimeError: If the C constructor fails (propagated from base class).
        """
        if len(block_hash) != 32:
            raise ValueError(
                f"block_hash argument must be bytes of length 32, got {len(block_hash)}"
            )
        hash_array = (ctypes.c_ubyte * 32).from_buffer_copy(block_hash)
        super().__init__(hash_array)

    def __bytes__(self) -> bytes:
        """Serialize the block hash to bytes.

        Returns:
            The 32-byte block hash in little-endian byte order.
        """
        hash_array = (ctypes.c_ubyte * 32)()
        k.btck_block_hash_to_bytes(self, hash_array)
        return bytes(hash_array)

    def __str__(self) -> str:
        """Get the hexadecimal representation of the block hash.

        Returns:
            The block hash as a 64-character hex string in big-endian
            byte order (standard Bitcoin display format).
        """
        # bytes are serialized in little-endian byte order, typically displayed in big-endian byte order
        return bytes(self)[::-1].hex()

    def __eq__(self, other: object) -> bool:
        """Check equality with another block hash.

        Args:
            other: Object to compare with.

        Returns:
            True if both are BlockHash instances with equal values.
        """
        if isinstance(other, BlockHash):
            return bool(k.btck_block_hash_equals(self, other))
        return False

    def __hash__(self) -> int:
        """Get hash value for use in sets and dictionaries.

        Returns:
            Hash of the block hash bytes.
        """
        return hash(bytes(self))

    def __repr__(self) -> str:
        """Return a string representation of the block hash."""
        return f"BlockHash({bytes(self)!r})"


class BlockTreeEntry(KernelOpaquePtr):
    """Entry in the block tree.

    A block tree entry represents a single block in the block tree
    maintained by the chainstate manager. Each entry (except genesis)
    points to a single parent, and multiple entries may share a parent,
    forming a tree structure. Each entry corresponds to a single block
    and may be used to retrieve its data and validation status.
    """

    @property
    def block_hash(self) -> BlockHash:
        """The hash of the block this entry represents.

        Returns:
            The block hash associated with this entry.
        """
        return BlockHash._from_view(k.btck_block_tree_entry_get_block_hash(self))

    @property
    def height(self) -> int:
        """The height of this block in the chain.

        Returns:
            The block height. Genesis block is at height 0.
        """
        return k.btck_block_tree_entry_get_height(self)

    @property
    def previous(self) -> "BlockTreeEntry":
        """The parent block tree entry.

        Returns:
            The previous block tree entry in the tree.

        Raises:
            RuntimeError: If the C constructor fails (propagated from base class).
        """
        return BlockTreeEntry._from_view(k.btck_block_tree_entry_get_previous(self))

    def __eq__(self, other: object) -> bool:
        """Check equality with another block tree entry.

        Args:
            other: Object to compare with.

        Returns:
            True if both are BlockTreeEntry instances with equal height and hash.
        """
        if isinstance(other, BlockTreeEntry):
            return self.height == other.height and self.block_hash == other.block_hash
        return False

    def __hash__(self) -> int:
        """Get hash value for use in sets and dictionaries.

        Returns:
            Hash combining height and block hash.
        """
        return hash((self.height, bytes(self.block_hash)))

    def __repr__(self) -> str:
        """Return a string representation of the block tree entry."""
        return f"<BlockTreeEntry height={self.height} hash={str(self.block_hash)}>"


class TransactionSequence(LazySequence[Transaction]):
    """Lazily-evaluated sequence of transactions in a block.

    This sequence provides indexed access to transactions within a block.
    The sequence is a view into the block and caches its length on first access.
    """

    def __init__(self, block: "Block"):
        """Create a sequence view of transactions.

        Args:
            block: The block to create a sequence view for.
        """
        self._block = block

    def __len__(self) -> int:
        """Number of transactions in the block.

        Returns:
            The transaction count (cached after first call).
        """
        if not hasattr(self, "_cached_len"):
            self._cached_len = k.btck_block_count_transactions(self._block)
        return self._cached_len

    def _get_item(self, index: int) -> Transaction:
        """Get the transaction at the given index."""
        return Transaction._from_view(
            k.btck_block_get_transaction_at(self._block, index), self._block
        )


class Block(KernelOpaquePtr):
    """A deserialized Bitcoin block."""

    _create_fn = k.btck_block_create
    _destroy_fn = k.btck_block_destroy

    def __init__(self, raw_block: bytes):
        """Create a block from serialized data.

        Args:
            raw_block: The serialized block data in consensus format.

        Raises:
            RuntimeError: If parsing the block data fails (propagated from base class).
        """
        super().__init__((ctypes.c_ubyte * len(raw_block))(*raw_block), len(raw_block))

    @property
    def block_hash(self) -> BlockHash:
        """The hash of this block.

        Computes the double-SHA256 hash of the block header.

        Returns:
            The block hash.
        """
        return BlockHash._from_handle(k.btck_block_get_hash(self))

    def __bytes__(self) -> bytes:
        """Serialize the block to bytes.

        Returns:
            The serialized block data in consensus format, suitable for
            P2P network transmission.
        """
        writer = ByteWriter()
        return writer.write(k.btck_block_to_bytes, self)

    def _get_transaction_at(self, transaction_index: int) -> Transaction:
        """Get the transaction at the given index."""
        return Transaction._from_view(
            k.btck_block_get_transaction_at(self, transaction_index), self
        )

    @property
    def transactions(self) -> TransactionSequence:
        """All transactions in this block.

        Returns:
            A lazy sequence of transactions, including the coinbase.
        """
        return TransactionSequence(self)

    def __repr__(self) -> str:
        """Return a string representation of the block."""
        return f"<Block hash={str(self.block_hash)} txs={len(self.transactions)}>"


class TransactionSpentOutputsSequence(LazySequence[TransactionSpentOutputs]):
    """Lazily-evaluated sequence of spent outputs for transactions in a block.

    This sequence provides indexed access to the spent outputs (undo data)
    for each transaction in a block. The sequence excludes the coinbase
    transaction, which has no spent outputs.
    """

    def __init__(self, block_spent_outputs: "BlockSpentOutputs"):
        """Create a sequence view of transaction spent outputs.

        Args:
            block_spent_outputs: The block spent outputs to create a sequence view for.
        """
        self._block_spent_outputs = block_spent_outputs

    def __len__(self) -> int:
        """Number of transaction spent outputs in the block. Equals the number of transactions in
        the block, minus 1 because the coinbase transaction is excluded as it has no spent outputs.

        Returns:
            The count of transaction spent outputs (cached after first call).
        """
        if not hasattr(self, "_cached_len"):
            self._cached_len = k.btck_block_spent_outputs_count(
                self._block_spent_outputs
            )
        return self._cached_len

    def _get_item(self, index: int) -> TransactionSpentOutputs:
        """Get the transaction spent outputs at the given index."""
        ptr = k.btck_block_spent_outputs_get_transaction_spent_outputs_at(
            self._block_spent_outputs, index
        )
        return TransactionSpentOutputs._from_view(ptr, self._block_spent_outputs)


class BlockSpentOutputs(KernelOpaquePtr):
    """Spent outputs (undo data) for all transactions in a block.

    Block spent outputs contain all the previous outputs consumed by all
    transactions in a specific block. This data is also known as "undo data"
    because it's necessary for reverting blocks during chain reorganizations.
    The data is stored as a nested structure: a sequence of transaction spent
    outputs, each containing the coins consumed by that transaction's inputs.
    """

    # Non-instantiable but can own pointers when read from disk
    _destroy_fn = k.btck_block_spent_outputs_destroy

    def _get_transaction_spent_outputs_at(self, index: int) -> TransactionSpentOutputs:
        """Get the transaction spent outputs at the given index."""
        ptr = k.btck_block_spent_outputs_get_transaction_spent_outputs_at(self, index)
        return TransactionSpentOutputs._from_view(ptr, self)

    @property
    def transactions(self) -> TransactionSpentOutputsSequence:
        """Spent outputs for each transaction in the block.

        Returns:
            A sequence of transaction spent outputs, excluding the coinbase.
        """
        return TransactionSpentOutputsSequence(self)

    def __repr__(self) -> str:
        """Return a string representation of the block spent outputs."""
        return f"<BlockSpentOutputs txs={len(self.transactions)}>"
