import ctypes
import typing

import pbk.capi.bindings as k
from pbk.capi import KernelOpaquePtr
from pbk.script import ScriptPubkey


class Txid(KernelOpaquePtr):
    def __init__(self, *args, **kwargs):
        raise NotImplementedError()

    def to_bytes(self) -> bytes:
        hash_array = (ctypes.c_ubyte * 32)()
        k.btck_txid_to_bytes(self, hash_array)
        return bytes(hash_array)

    def __eq__(self, other: typing.Any):
        if not isinstance(other, Txid):
            return False
        return bool(k.btck_txid_equals(self, other))


class TransactionOutPoint(KernelOpaquePtr):
    def __init__(self, *args, **kwargs):
        raise NotImplementedError()

    @property
    def index(self) -> int:
        return k.btck_transaction_out_point_get_index(self)

    @property
    def txid(self) -> Txid:
        return Txid._from_view(k.btck_transaction_out_point_get_txid(self), self)


class TransactionInput(KernelOpaquePtr):
    def __init__(self, *args, **kwargs):
        raise NotImplementedError()

    @property
    def out_point(self) -> TransactionOutPoint:
        return TransactionOutPoint._from_view(
            k.btck_transaction_input_get_out_point(self), self
        )


class TransactionOutput(KernelOpaquePtr):
    def __init__(self, script_pubkey: "ScriptPubkey", amount: int):
        super().__init__(script_pubkey, amount)

    @property
    def amount(self) -> int:
        return k.btck_transaction_output_get_amount(self)

    @property
    def script_pubkey(self) -> "ScriptPubkey":
        ptr = k.btck_transaction_output_get_script_pubkey(self)
        return ScriptPubkey._from_view(ptr, self)


class Transaction(KernelOpaquePtr):
    def __init__(self, data: bytes):
        super().__init__((ctypes.c_ubyte * len(data))(*data), len(data))

    @property
    def input_count(self) -> int:
        return k.btck_transaction_count_inputs(self)

    @property
    def output_count(self) -> int:
        return k.btck_transaction_count_outputs(self)

    def get_input_at(self, input_index: int) -> TransactionInput:
        return TransactionInput._from_view(
            k.btck_transaction_get_input_at(self, input_index), self
        )

    def get_output_at(self, output_index) -> TransactionOutput:
        return TransactionOutput._from_view(
            k.btck_transaction_get_output_at(self, output_index), self
        )

    @property
    def txid(self) -> Txid:
        return Txid._from_view(k.btck_transaction_get_txid(self), self)


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
        return TransactionOutput._from_view(ptr, self)


class TransactionSpentOutputs(KernelOpaquePtr):
    def __init__(self, *args, **kwargs):
        raise NotImplementedError()

    @property
    def output_count(self) -> int:
        return k.btck_transaction_spent_outputs_count(self)

    def get_coin(self, index: int) -> Coin:
        ptr = k.btck_transaction_spent_outputs_get_coin_at(self, index)
        return Coin._from_view(ptr, self)

    def iter_outputs(self) -> typing.Generator["TransactionOutput", None, None]:
        for i in range(self.output_count):
            yield self.get_coin(i).output
