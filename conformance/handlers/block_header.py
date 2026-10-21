import copy

from conformance.protocol import Parameters
import pbk
import pbk.capi.bindings as k


def btck_block_header_create(params: Parameters) -> pbk.BlockHeader:
    return pbk.BlockHeader(bytes.fromhex(params["raw_block_header"]))


def btck_block_header_destroy(params: Parameters) -> None:
    params["header"].delete()


def btck_block_header_copy(params: Parameters) -> pbk.BlockHeader:
    return copy.copy(params["header"].value)


def btck_block_header_get_hash(params: Parameters) -> pbk.BlockHash:
    return params["header"].value.block_hash


def btck_block_header_get_prev_hash(params: Parameters) -> pbk.BlockHash:
    return params["header"].value.prev_hash


def btck_block_header_get_timestamp(params: Parameters) -> int:
    return k.btck_block_header_get_timestamp(params["header"].value)


def btck_block_header_get_bits(params: Parameters) -> int:
    return params["header"].value.bits


def btck_block_header_get_version(params: Parameters) -> int:
    return params["header"].value.version


def btck_block_header_get_nonce(params: Parameters) -> int:
    return params["header"].value.nonce


def btck_block_get_header(params: Parameters) -> pbk.BlockHeader:
    return params["block"].value.block_header
