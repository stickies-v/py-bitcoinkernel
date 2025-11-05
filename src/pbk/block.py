import ctypes
import typing

import pbk.capi.bindings as k
from pbk.capi import KernelOpaquePtr
from pbk.transaction import TransactionSpentOutputs
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
        return BlockHash._from_handle(k.btck_block_tree_entry_get_block_hash(self))

    @property
    def height(self) -> int:
        return k.btck_block_tree_entry_get_height(self)

    def __eq__(self, other):
        if isinstance(other, BlockIndex):
            return self.height == other.height and self.block_hash == other.block_hash
        return False

    def __repr__(self):  # pragma: no cover
        return f"BlockIndex(height={self.height}, hash={self.block_hash.hex})"


class Block(KernelOpaquePtr):
    def __init__(self, raw_block: bytes):
        super().__init__((ctypes.c_ubyte * len(raw_block))(*raw_block), len(raw_block))

    @property
    def hash(self) -> BlockHash:
        return BlockHash._from_handle(k.btck_block_get_hash(self))

    @property
    def data(self) -> bytes:
        writer = ByteWriter()
        return writer.write(k.btck_block_to_bytes, self)


class BlockSpentOutputs(KernelOpaquePtr):
    def __init__(self, *args, **kwargs):
        raise NotImplementedError(
            "BlockSpentOutputs cannot be constructed directly"
        )  # pragma: no cover

    @property
    def transaction_count(self) -> int:
        return k.btck_block_spent_outputs_count(self)

    def get_transaction_spent_outputs(self, index: int) -> TransactionSpentOutputs:
        ptr = k.btck_block_spent_outputs_get_transaction_spent_outputs_at(self, index)
        return TransactionSpentOutputs._from_view(ptr, self)

    def iter_transactions(
        self,
    ) -> typing.Generator[TransactionSpentOutputs, None, None]:
        """
        Generator that yields all the TransactionUndo objects in this
        BlockSpentOutputs.

        Synchronization is required if this generator is shared across
        threads.
        """
        for i in range(self.transaction_count):
            yield self.get_transaction_spent_outputs(i)
