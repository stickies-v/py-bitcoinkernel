import ctypes
import typing
from enum import IntEnum

import pbk.capi.bindings as k
from pbk.block import Block, BlockIndex, BlockUndo
from pbk.capi import KernelOpaquePtr

if typing.TYPE_CHECKING:
    from pbk import BlockHash, Context


class ChainType(IntEnum):
    MAINNET = k.kernel_CHAIN_TYPE_MAINNET
    TESTNET = k.kernel_CHAIN_TYPE_TESTNET
    TESTNET_4 = k.kernel_CHAIN_TYPE_TESTNET_4
    SIGNET = k.kernel_CHAIN_TYPE_SIGNET
    REGTEST = k.kernel_CHAIN_TYPE_REGTEST


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
        return k.kernel_chainstate_manager_options_set_wipe_dbs(
            self, wipe_block_tree_db, wipe_chainstate_db
        )

    def set_worker_threads_num(self, worker_threads: int):
        k.kernel_chainstate_manager_options_set_worker_threads_num(self, worker_threads)


class ChainstateManager(KernelOpaquePtr):
    _context: "Context"  # Persisted to ensure context is not destroyed before ChainstateManager

    def __init__(
        self,
        context: "Context",
        chain_man_opts: ChainstateManagerOptions,
    ):
        self._context = context
        super().__init__(context, chain_man_opts)

    def get_block_index_from_hash(self, hash: "BlockHash"):
        return BlockIndex._from_ptr(
            k.kernel_get_block_index_from_hash(self._context, self, hash)
        )

    def get_block_index_from_height(self, height: int):
        return BlockIndex._from_ptr(
            k.kernel_get_block_index_from_height(self._context, self, height)
        )

    def get_block_index_from_genesis(self) -> "BlockIndex":
        return BlockIndex._from_ptr(
            k.kernel_get_block_index_from_genesis(self._context, self)
        )

    def get_block_index_from_tip(self) -> "BlockIndex":
        return BlockIndex._from_ptr(
            k.kernel_get_block_index_from_tip(self._context, self)
        )

    def get_next_block_index(self, block_index: "BlockIndex") -> "BlockIndex | None":
        next = k.kernel_get_next_block_index(self._context, self, block_index)
        return BlockIndex._from_ptr(next) if next else None

    def get_previous_block_index(
        self, block_index: "BlockIndex"
    ) -> "BlockIndex | None":
        previous = k.kernel_get_previous_block_index(block_index)
        return BlockIndex._from_ptr(previous) if previous else None

    def process_block(self, block: Block, new_block: bool | None) -> bool:
        new_block_ptr = (
            ctypes.pointer(ctypes.c_bool(new_block)) if new_block is not None else None
        )
        return k.kernel_chainstate_manager_process_block(
            self._context, self, block, new_block_ptr
        )

    def read_block_from_disk(self, block_index: "BlockIndex") -> Block:
        block = k.kernel_read_block_from_disk(self._context, self, block_index)
        if not block:
            raise RuntimeError(f"Error reading block for {block_index} from disk")
        return Block._from_ptr(block)

    def read_block_undo_from_disk(self, block_index: "BlockIndex") -> BlockUndo:
        if block_index.height == 0:
            raise ValueError("Genesis block does not have undo data")

        undo = k.kernel_read_block_undo_from_disk(self._context, self, block_index)
        if not undo:
            raise RuntimeError(f"Error reading block undo for {block_index} from disk")
        return BlockUndo._from_ptr(undo)

    def _destroy(self):
        self._auto_kernel_fn("destroy", self, self._context)


def block_index_generator(
    chain_man: ChainstateManager,
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
        start = chain_man.get_block_index_from_genesis()
    elif isinstance(start, int):
        tip_height = chain_man.get_block_index_from_tip().height
        if start < 0:
            start = tip_height + start + 1
        if start < 0 or start > tip_height:
            raise IndexError(
                f"Start height {start} is out of bounds for tip height {tip_height}"
            )
        start = chain_man.get_block_index_from_height(start)

    if end is None:
        end = chain_man.get_block_index_from_tip()
    elif isinstance(end, int):
        tip_height = chain_man.get_block_index_from_tip().height
        if end < 0:
            end = tip_height + end + 1
        if end < 0 or end > tip_height:
            raise IndexError(
                f"End height {end} is out of bounds for tip height {tip_height}"
            )
        end = chain_man.get_block_index_from_height(end)

    next = start

    if start.height <= end.height:
        iter_func = chain_man.get_next_block_index
    else:
        iter_func = chain_man.get_previous_block_index

    while next:
        yield next
        next = iter_func(next) if next != end else None
