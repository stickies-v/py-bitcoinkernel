import ctypes
import typing

import pbk.capi.bindings as k
from pbk.capi import KernelOpaquePtr
from pbk.script import ScriptPubkey
from pbk.util.sequence import LazySequence
from pbk.writer import ByteWriter


class Txid(KernelOpaquePtr):
    def __init__(self, *args, **kwargs):
        raise NotImplementedError()

    def __bytes__(self) -> bytes:
        hash_array = (ctypes.c_ubyte * 32)()
        k.btck_txid_to_bytes(self, hash_array)
        return bytes(hash_array)

    def __eq__(self, other: typing.Any):
        if not isinstance(other, Txid):
            return False
        return bool(k.btck_txid_equals(self, other))

    def __hash__(self) -> int:
        return hash(bytes(self))

    def __str__(self) -> str:
        # bytes are serialized in little-endian byte order, typically displayed in big-endian byte order
        return bytes(self)[::-1].hex()


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


class TransactionInputSequence(LazySequence[TransactionInput]):
    def __init__(self, transaction: "Transaction"):
        self._transaction = transaction

    def __len__(self) -> int:
        if not hasattr(self, "_cached_len"):
            self._cached_len = k.btck_transaction_count_inputs(self._transaction)
        return self._cached_len

    def _get_item(self, index: int) -> TransactionInput:
        return TransactionInput._from_view(
            k.btck_transaction_get_input_at(self._transaction, index), self._transaction
        )


class TransactionOutputSequence(LazySequence[TransactionOutput]):
    def __init__(self, transaction: "Transaction"):
        self._transaction = transaction

    def __len__(self) -> int:
        if not hasattr(self, "_cached_len"):
            self._cached_len = k.btck_transaction_count_outputs(self._transaction)
        return self._cached_len

    def _get_item(self, index: int) -> TransactionOutput:
        return TransactionOutput._from_view(
            k.btck_transaction_get_output_at(self._transaction, index),
            self._transaction,
        )


class Transaction(KernelOpaquePtr):
    def __init__(self, data: bytes):
        super().__init__((ctypes.c_ubyte * len(data))(*data), len(data))

    def _get_input_at(self, index: int) -> TransactionInput:
        return TransactionInput._from_view(
            k.btck_transaction_get_input_at(self, index), self
        )

    def _get_output_at(self, index: int) -> TransactionOutput:
        return TransactionOutput._from_view(
            k.btck_transaction_get_output_at(self, index), self
        )

    @property
    def inputs(self) -> TransactionInputSequence:
        return TransactionInputSequence(self)

    @property
    def outputs(self) -> TransactionOutputSequence:
        return TransactionOutputSequence(self)

    @property
    def txid(self) -> Txid:
        return Txid._from_view(k.btck_transaction_get_txid(self), self)

    def __bytes__(self) -> bytes:
        writer = ByteWriter()
        return writer.write(k.btck_transaction_to_bytes, self)


class Coin(KernelOpaquePtr):
    def __init__(self, *args, **kwargs):
        raise NotImplementedError()

    @property
    def confirmation_height(self) -> int:
        return k.btck_coin_confirmation_height(self)

    @property
    def is_coinbase(self) -> bool:
        res = k.btck_coin_is_coinbase(self)
        assert res in [0, 1]
        return bool(res)

    @property
    def output(self) -> TransactionOutput:
        ptr = k.btck_coin_get_output(self)
        return TransactionOutput._from_view(ptr, self)


class CoinSequence(LazySequence[Coin]):
    def __init__(self, spent_outputs: "TransactionSpentOutputs"):
        self._spent_outputs = spent_outputs

    def __len__(self) -> int:
        if not hasattr(self, "_cached_len"):
            self._cached_len = k.btck_transaction_spent_outputs_count(
                self._spent_outputs
            )
        return self._cached_len

    def _get_item(self, index: int) -> Coin:
        ptr = k.btck_transaction_spent_outputs_get_coin_at(self._spent_outputs, index)
        return Coin._from_view(ptr, self._spent_outputs)


class TransactionSpentOutputs(KernelOpaquePtr):
    def __init__(self, *args, **kwargs):
        raise NotImplementedError()

    def _get_coin_at(self, index: int) -> Coin:
        ptr = k.btck_transaction_spent_outputs_get_coin_at(self, index)
        return Coin._from_view(ptr, self)

    @property
    def coins(self) -> CoinSequence:
        return CoinSequence(self)
