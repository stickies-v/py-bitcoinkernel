import ctypes
import typing

import pbk.capi.bindings as k
import pbk.util.type
from pbk.capi import KernelOpaquePtr, KernelPtr
from pbk.transaction import TransactionUndo


class BlockHash(KernelPtr):
    @property
    def bytes(self) -> bytes:
        return bytes(self.contents.hash)

    @property
    def hex(self) -> str:
        return self.bytes.hex()

    def __eq__(self, other):
        if isinstance(other, BlockHash):
            return self.bytes == other.bytes
        return False


class BlockIndex(KernelOpaquePtr):
    def __init__(self, *args, **kwargs):
        raise NotImplementedError(
            "BlockIndex needs to be constructed via its `from_*` factory methods"
        )

    @property
    def block_hash(self) -> BlockHash:
        return BlockHash._from_ptr(k.kernel_block_index_get_block_hash(self))

    @property
    def height(self) -> int:
        return self._auto_kernel_fn("get_height", self)

    def __eq__(self, other):
        if isinstance(other, BlockIndex):
            return self.height == other.height and self.block_hash == other.block_hash
        return False

    def __repr__(self):
        return f"BlockIndex(height={self.height}, hash={self.block_hash.hex})"


class Block(KernelOpaquePtr):
    def __init__(self, raw_block: bytes):
        super().__init__((ctypes.c_ubyte * len(raw_block))(*raw_block), len(raw_block))

    @property
    def hash(self) -> BlockHash:
        return BlockHash._from_ptr(k.kernel_block_get_hash(self))

    @property
    def data(self) -> bytes:
        bytearray = pbk.util.ByteArray._from_ptr(k.kernel_copy_block_data(self))
        return bytearray.data


class BlockUndo(KernelOpaquePtr):
    def __init__(self, *args, **kwargs):
        raise NotImplementedError("BlockUndo cannot be constructed directly")

    @property
    def transaction_count(self) -> int:
        return k.kernel_block_undo_size(self)

    def iter_transactions(self) -> typing.Generator[TransactionUndo, None, None]:
        for i in range(self.transaction_count):
            yield TransactionUndo(self, i)
