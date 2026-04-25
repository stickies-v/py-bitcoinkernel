from conformance.protocol import Parameters
import pbk


def btck_chain_get_height(params: Parameters) -> int:
    chain: pbk.Chain = params["chain"].value
    return chain.height


def btck_chain_get_by_height(params: Parameters) -> pbk.BlockTreeEntry:
    chain: pbk.Chain = params["chain"].value
    return chain.block_tree_entries[int(params["block_height"])]


def btck_chain_contains(params: Parameters) -> bool:
    chain: pbk.Chain = params["chain"].value
    entry: pbk.BlockTreeEntry = params["block_tree_entry"].value

    return entry in chain.block_tree_entries
