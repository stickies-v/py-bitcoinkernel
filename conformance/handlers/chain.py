from conformance.protocol import Parameters
import pbk


def btck_chain_get_height(params: Parameters) -> int:
    return params["chain"].value.height


def btck_chain_get_by_height(params: Parameters) -> pbk.BlockTreeEntry:
    return params["chain"].value.block_tree_entries[int(params["block_height"])]


def btck_chain_contains(params: Parameters) -> bool:
    return params["block_tree_entry"].value in params["chain"].value.block_tree_entries
