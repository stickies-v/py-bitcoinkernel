import ctypes
import typing

import pbk.capi.bindings as k
from pbk.capi import KernelOpaquePtr

if typing.TYPE_CHECKING:
    from pbk.block import BlockUndo
    from pbk.script import ScriptPubkey

class Transaction(KernelOpaquePtr):
    def __init__(self, data: bytes):
        super().__init__((ctypes.c_ubyte * len(data))(*data), len(data))


class TransactionOutput(KernelOpaquePtr):
    def __init__(self, script_pubkey: "ScriptPubkey", amount: int):
        super().__init__(script_pubkey, amount)

    @classmethod
    def from_undo(cls, undo: "BlockUndo", transaction_index: int, output_index: int) -> "TransactionOutput":
        return cls._from_ptr(k.kernel_get_undo_output_by_index(undo, transaction_index, output_index))

    @property
    def amount(self) -> int:
        return k.kernel_get_transaction_output_amount(self)

    @property
    def script_pubkey(self) -> "ScriptPubkey":
        return ScriptPubkey._from_ptr(k.kernel_copy_script_pubkey_from_output(self))
