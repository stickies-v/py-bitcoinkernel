import ctypes
import typing

import pbk.capi.bindings as k
from pbk.capi import KernelOpaquePtr
from pbk.script import ScriptPubkey

if typing.TYPE_CHECKING:
    from pbk.block import BlockUndo


class Transaction(KernelOpaquePtr):
    def __init__(self, data: bytes):
        super().__init__((ctypes.c_ubyte * len(data))(*data), len(data))


class TransactionOutput(KernelOpaquePtr):
    def __init__(self, script_pubkey: "ScriptPubkey", amount: int):
        super().__init__(script_pubkey, amount)

    @classmethod
    def from_undo(
        cls, undo: "BlockUndo", transaction_index: int, output_index: int
    ) -> "TransactionOutput":
        return cls._from_ptr(
            k.kernel_get_undo_output_by_index(undo, transaction_index, output_index)
        )

    @property
    def amount(self) -> int:
        return k.kernel_get_transaction_output_amount(self)

    @property
    def script_pubkey(self) -> "ScriptPubkey":
        return ScriptPubkey._from_ptr(k.kernel_copy_script_pubkey_from_output(self))


class TransactionUndo:
    """Helper class, does not exist in libbitcoinkernel"""

    def __init__(self, undo: "BlockUndo", transaction_index: int):
        self._undo = undo
        self._transaction_index = transaction_index

    @property
    def output_count(self) -> int:
        return k.kernel_get_transaction_undo_size(self._undo, self._transaction_index)

    def iter_outputs(self) -> typing.Generator["TransactionOutput", None, None]:
        for i in range(self.output_count):
            yield TransactionOutput.from_undo(self._undo, self._transaction_index, i)
