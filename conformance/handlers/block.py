import copy

from conformance.protocol import Parameters
import pbk


def btck_block_create(params: Parameters) -> pbk.Block:
    return pbk.Block(bytes.fromhex(params["raw_block"]))


def btck_block_destroy(params: Parameters) -> None:
    params["block"].delete()


def btck_block_copy(params: Parameters) -> pbk.Block:
    return copy.copy(params["block"].value)


def btck_block_to_bytes(params: Parameters) -> str:
    return bytes(params["block"].value).hex()


def btck_block_get_hash(params: Parameters) -> pbk.BlockHash:
    return params["block"].value.block_hash


def btck_block_count_transactions(params: Parameters) -> int:
    return len(params["block"].value.transactions)


def btck_block_get_transaction_at(params: Parameters) -> pbk.Transaction:
    return params["block"].value.transactions[int(params["transaction_index"])]


def btck_block_tree_entry_get_block_hash(params: Parameters) -> pbk.BlockHash:
    return params["block_tree_entry"].value.block_hash
