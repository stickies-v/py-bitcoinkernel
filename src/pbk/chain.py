import ctypes
import typing
from enum import IntEnum
from pathlib import Path

import pbk.capi.bindings as k
from pbk.block import Block, BlockIndex, BlockSpentOutputs
from pbk.capi import KernelOpaquePtr

if typing.TYPE_CHECKING:
    from pbk import BlockHash, Context


# TODO: add enum auto-generation or testing to ensure it remains in
# sync with bitcoinkernel.h
class ChainType(IntEnum):
    MAINNET = 0  # btck_ChainType_MAINNET
    TESTNET = 1  # btck_ChainType_TESTNET
    TESTNET_4 = 2  # btck_ChainType_TESTNET_4
    SIGNET = 3  # btck_ChainType_SIGNET
    REGTEST = 4  # btck_ChainType_REGTEST


class ChainParameters(KernelOpaquePtr):
    def __init__(self, chain_type: ChainType):
        super().__init__(chain_type)


class ChainstateManagerOptions(KernelOpaquePtr):
    def __init__(self, context: "Context", datadir: str, blocks_dir: str):
        datadir_bytes = datadir.encode("utf-8")
        blocksdir_bytes = blocks_dir.encode("utf-8")
        super().__init__(
            context,
            datadir_bytes,
            len(datadir_bytes),
            blocksdir_bytes,
            len(blocksdir_bytes),
        )

    def set_wipe_dbs(self, wipe_block_tree_db: bool, wipe_chainstate_db: bool) -> bool:
        return k.btck_chainstate_manager_options_set_wipe_dbs(
            self, wipe_block_tree_db, wipe_chainstate_db
        )

    def set_worker_threads_num(self, worker_threads: int):
        k.btck_chainstate_manager_options_set_worker_threads_num(self, worker_threads)


class Chain(KernelOpaquePtr):
    def get_tip(self) -> BlockIndex:
        return BlockIndex._from_view(k.btck_chain_get_tip(self))

    def current_height(self) -> int:
        return self.get_tip().height

    def get_genesis(self) -> BlockIndex:
        return BlockIndex._from_view(k.btck_chain_get_genesis(self))

    def get_by_height(self, height: int) -> BlockIndex:
        return BlockIndex._from_view(k.btck_chain_get_by_height(self, height))

    def contains(self, entry: BlockIndex) -> bool:
        result: int = k.btck_chain_contains(self, entry)
        assert result in [0, 1]
        return bool(result)


class ChainstateManager(KernelOpaquePtr):
    def __init__(
        self,
        chain_man_opts: ChainstateManagerOptions,
    ):
        super().__init__(chain_man_opts)

    def get_block_index_from_hash(self, hash: "BlockHash"):
        return BlockIndex._from_view(
            k.btck_chainstate_manager_get_block_tree_entry_by_hash(self, hash)
        )

    def get_active_chain(self) -> Chain:
        return Chain._from_view(k.btck_chainstate_manager_get_active_chain(self))

    def import_blocks(self, paths: typing.List[Path]) -> bool:
        encoded_paths = [str(path).encode("utf-8") for path in paths]

        block_file_paths = (ctypes.c_char_p * len(encoded_paths))()
        block_file_paths[:] = encoded_paths
        block_file_paths_lens = (ctypes.c_size_t * len(encoded_paths))()
        block_file_paths_lens[:] = [len(path) for path in encoded_paths]

        return k.btck_chainstate_manager_import_blocks(
            self,
            ctypes.cast(
                block_file_paths, ctypes.POINTER(ctypes.POINTER(ctypes.c_char))
            ),
            block_file_paths_lens,
            len(paths),
        )

    def process_block(self, block: Block, new_block: int | None) -> bool:
        new_block_ptr = (
            ctypes.pointer(ctypes.c_int(new_block)) if new_block is not None else None
        )
        return k.btck_chainstate_manager_process_block(self, block, new_block_ptr)

    def read_block_from_disk(self, block_index: "BlockIndex") -> Block:
        block = k.btck_block_read(self, block_index)
        if not block:
            raise RuntimeError(f"Error reading block for {block_index} from disk")
        return Block._from_handle(block)

    def read_block_undo_from_disk(self, block_index: "BlockIndex") -> BlockSpentOutputs:
        if block_index.height == 0:
            raise ValueError("Genesis block does not have undo data")

        undo = k.btck_block_spent_outputs_read(self, block_index)
        if not undo:
            raise RuntimeError(f"Error reading block undo for {block_index} from disk")
        return BlockSpentOutputs._from_handle(undo)


def block_index_generator(
    chain: Chain,
    start: "BlockIndex | int | None" = None,  # default to genesis
    end: "BlockIndex | int | None" = None,  # default to chaintip
) -> typing.Generator[BlockIndex, typing.Any, None]:
    """Iterate over BlockIndexes from start (inclusive, defaults to genesis) to end (inclusive,
    defaults to chaintip).

    @param start: BlockIndex or int. If int is provided, it represents the block height.
                  Negative integers are supported and count backwards from the tip
                  (e.g. -1 means the last block, -2 second to last, etc.).
                  If None, starts from genesis block.
    @param end: BlockIndex or int. If int is provided, it represents the block height.
                Negative integers are supported and count backwards from the tip
                (e.g. -1 means the last block, -2 second to last, etc.).
                If None, ends at the current chain tip.
    @return: Generator[BlockIndex, Any, None] that yields BlockIndex objects in sequence.
             The sequence can go either forward or backward depending on whether
             start.height <= end.height.
    @raises IndexError: If the provided start or end heights are out of bounds
    """
    if start is None:
        start = chain.get_genesis()
    elif isinstance(start, int):
        tip_height = chain.get_tip().height
        if start < 0:
            start = tip_height + start + 1
        if start < 0 or start > tip_height:
            raise IndexError(
                f"Start height {start} is out of bounds for tip height {tip_height}"
            )
        start = chain.get_by_height(start)

    if end is None:
        end = chain.get_tip()
    elif isinstance(end, int):
        tip_height = chain.get_tip().height
        if end < 0:
            end = tip_height + end + 1
        if end < 0 or end > tip_height:
            raise IndexError(
                f"End height {end} is out of bounds for tip height {tip_height}"
            )
        end = chain.get_by_height(end)

    next = start
    direction = 1 if start.height <= end.height else -1

    while next:
        yield next
        next = chain.get_by_height(next.height + direction) if next != end else None
