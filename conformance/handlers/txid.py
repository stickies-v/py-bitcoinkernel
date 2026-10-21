import copy

from conformance.protocol import Parameters
import pbk


def btck_txid_destroy(params: Parameters) -> None:
    params["txid"].delete()


def btck_txid_copy(params: Parameters) -> pbk.Txid:
    return copy.copy(params["txid"].value)


def btck_txid_to_bytes(params: Parameters) -> str:
    return bytes(params["txid"].value).hex()


def btck_txid_equals(params: Parameters) -> bool:
    return params["txid1"].value == params["txid2"].value
