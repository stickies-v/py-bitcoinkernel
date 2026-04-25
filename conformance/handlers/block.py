from conformance.protocol import Parameters
import pbk


def btck_block_create(params: Parameters) -> pbk.Block:
    return pbk.Block(bytes.fromhex(params["raw_block"]))


def btck_block_tree_entry_get_block_hash(params: Parameters) -> str:
    entry: pbk.BlockTreeEntry = params["block_tree_entry"].value
    return str(entry.block_hash)
