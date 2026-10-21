import copy

from conformance.protocol import Parameters
import pbk


def btck_block_hash_create(params: Parameters) -> pbk.BlockHash:
    return pbk.BlockHash(bytes.fromhex(params["block_hash"]))


def btck_block_hash_destroy(params: Parameters) -> None:
    params["block_hash"].delete()


def btck_block_hash_copy(params: Parameters) -> pbk.BlockHash:
    return copy.copy(params["block_hash"].value)


def btck_block_hash_to_bytes(params: Parameters) -> str:
    return bytes(params["block_hash"].value).hex()


def btck_block_hash_equals(params: Parameters) -> bool:
    return params["hash1"].value == params["hash2"].value
