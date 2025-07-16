import ctypes
import typing

import pbk.capi.bindings as k
from pbk.capi import KernelOpaquePtr
from pbk.script import ScriptPubkey


class Transaction(KernelOpaquePtr):
    def __init__(self, data: bytes):
        super().__init__((ctypes.c_ubyte * len(data))(*data), len(data))


class TransactionOutput(KernelOpaquePtr):
    def __init__(self, script_pubkey: "ScriptPubkey", amount: int):
        super().__init__(script_pubkey, amount)

    @property
    def amount(self) -> int:
        return k.btck_transaction_output_get_amount(self)

    @property
    def script_pubkey(self) -> "ScriptPubkey":
        ptr = k.btck_transaction_output_get_script_pubkey(self)
        return ScriptPubkey._from_ptr(ptr, owns_ptr=False, parent=self)


class Coin(KernelOpaquePtr):
    def __init__(self, *args, **kwargs):
        raise NotImplementedError()

    @property
    def confirmation_height(self) -> int:
        return k.btck_coin_confirmation_height(self)

    @property
    def is_coinbase(self) -> bool:
        res = k.btck_coin_is_coinbase()
        assert res in [0, 1]
        return bool(res)

    @property
    def output(self) -> TransactionOutput:
        ptr = k.btck_coin_get_output(self)
        return TransactionOutput._from_ptr(ptr, owns_ptr=False, parent=self)


class TransactionSpentOutputs(KernelOpaquePtr):
    def __init__(self, *args, **kwargs):
        raise NotImplementedError()

    @property
    def output_count(self) -> int:
        return k.btck_transaction_spent_outputs_count(self)

    def get_coin(self, index: int) -> Coin:
        ptr = k.btck_transaction_spent_outputs_get_coin_at(self, index)
        return Coin._from_ptr(ptr, owns_ptr=False, parent=self)

    def iter_outputs(self) -> typing.Generator["TransactionOutput", None, None]:
        for i in range(self.output_count):
            yield self.get_coin(i).output
