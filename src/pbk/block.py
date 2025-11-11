import ctypes

import pbk.capi.bindings as k
from pbk.capi import KernelOpaquePtr
from pbk.transaction import Transaction, TransactionSpentOutputs
from pbk.util.sequence import LazySequence
from pbk.writer import ByteWriter


class BlockHash(KernelOpaquePtr):
    def __init__(self, block_hash: bytes):
        if len(block_hash) != 32:
            raise ValueError(
                f"block_hash argument must be bytes of length 32, got {len(block_hash)}"
            )
        hash_array = (ctypes.c_ubyte * 32).from_buffer_copy(block_hash)
        super().__init__(hash_array)

    @property
    def bytes(self) -> bytes:
        hash_array = (ctypes.c_ubyte * 32)()
        k.btck_block_hash_to_bytes(self, hash_array)
        return bytes(hash_array)

    @property
    def hex(self) -> str:
        return self.bytes.hex()

    def __eq__(self, other):
        if isinstance(other, BlockHash):
            return bool(k.btck_block_hash_equals(self, other))
        return False


class BlockIndex(KernelOpaquePtr):
    def __init__(self, *args, **kwargs):
        raise NotImplementedError(  # pragma: no cover
            "BlockIndex needs to be constructed via its `from_*` factory methods"
        )

    @property
    def block_hash(self) -> BlockHash:
        return BlockHash._from_view(k.btck_block_tree_entry_get_block_hash(self))

    @property
    def height(self) -> int:
        return k.btck_block_tree_entry_get_height(self)

    def __eq__(self, other):
        if isinstance(other, BlockIndex):
            return self.height == other.height and self.block_hash == other.block_hash
        return False

    def __repr__(self):  # pragma: no cover
        return f"BlockIndex(height={self.height}, hash={self.block_hash.hex})"


class TransactionSequence(LazySequence[Transaction]):
    def __init__(self, block: "Block"):
        self._block = block

    def __len__(self) -> int:
        if not hasattr(self, "_cached_len"):
            self._cached_len = k.btck_block_count_transactions(self._block)
        return self._cached_len

    def _get_item(self, index: int) -> Transaction:
        return Transaction._from_view(
            k.btck_block_get_transaction_at(self._block, index), self._block
        )


class Block(KernelOpaquePtr):
    def __init__(self, raw_block: bytes):
        super().__init__((ctypes.c_ubyte * len(raw_block))(*raw_block), len(raw_block))

    @property
    def block_hash(self) -> BlockHash:
        return BlockHash._from_handle(k.btck_block_get_hash(self))

    @property
    def data(self) -> bytes:
        writer = ByteWriter()
        return writer.write(k.btck_block_to_bytes, self)

    def _get_transaction_at(self, transaction_index: int) -> Transaction:
        return Transaction._from_view(
            k.btck_block_get_transaction_at(self, transaction_index), self
        )

    @property
    def transactions(self) -> TransactionSequence:
        return TransactionSequence(self)


class TransactionSpentOutputsSequence(LazySequence[TransactionSpentOutputs]):
    def __init__(self, block_spent_outputs: "BlockSpentOutputs"):
        self._block_spent_outputs = block_spent_outputs

    def __len__(self) -> int:
        if not hasattr(self, "_cached_len"):
            self._cached_len = k.btck_block_spent_outputs_count(
                self._block_spent_outputs
            )
        return self._cached_len

    def _get_item(self, index: int) -> TransactionSpentOutputs:
        ptr = k.btck_block_spent_outputs_get_transaction_spent_outputs_at(
            self._block_spent_outputs, index
        )
        return TransactionSpentOutputs._from_view(ptr, self._block_spent_outputs)


class BlockSpentOutputs(KernelOpaquePtr):
    def __init__(self, *args, **kwargs):
        raise NotImplementedError(
            "BlockSpentOutputs cannot be constructed directly"
        )  # pragma: no cover

    def _get_transaction_spent_outputs_at(self, index: int) -> TransactionSpentOutputs:
        ptr = k.btck_block_spent_outputs_get_transaction_spent_outputs_at(self, index)
        return TransactionSpentOutputs._from_view(ptr, self)

    @property
    def transactions(self) -> TransactionSpentOutputsSequence:
        return TransactionSpentOutputsSequence(self)
