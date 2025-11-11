import ctypes
import typing
from enum import IntEnum
from pathlib import Path

import pbk.capi.bindings as k
from pbk.block import Block, BlockHash, BlockIndex, BlockSpentOutputs
from pbk.capi import KernelOpaquePtr
from pbk.util.sequence import LazySequence

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

    def update_block_tree_db_in_memory(self, block_tree_db_in_memory: bool):
        k.btck_chainstate_manager_options_update_block_tree_db_in_memory(
            self, int(block_tree_db_in_memory)
        )

    def update_chainstate_db_in_memory(self, chainstate_db_in_memory: bool):
        k.btck_chainstate_manager_options_update_chainstate_db_in_memory(
            self, int(chainstate_db_in_memory)
        )


class BlockIndexSequence(LazySequence[BlockIndex]):
    def __init__(self, chain: "Chain"):
        self._chain = chain

    def __len__(self) -> int:
        return len(self._chain)

    def _get_item(self, index: int) -> BlockIndex:
        return BlockIndex._from_view(k.btck_chain_get_by_height(self._chain, index))

    def __contains__(self, other: typing.Any):
        if not isinstance(other, BlockIndex):
            return False
        result = k.btck_chain_contains(self._chain, other)
        assert result in [0, 1]
        return bool(result)


class Chain(KernelOpaquePtr):
    def __init__(self, *args, **kwargs):
        raise NotImplementedError()

    @property
    def height(self) -> int:
        """Zero-based indexed height of the chain tip"""
        return k.btck_chain_get_height(self)

    def _get_by_height(self, height: int) -> BlockIndex:
        return BlockIndex._from_view(k.btck_chain_get_by_height(self, height))

    @property
    def block_indexes(self) -> BlockIndexSequence:
        return BlockIndexSequence(self)

    def __len__(self) -> int:
        # height is zero-based indexed
        return self.height + 1


class MapBase:
    def __init__(self, chainman: "ChainstateManager"):
        self._chainman = chainman


class BlockIndexMap(MapBase):
    def __getitem__(self, key: BlockHash) -> BlockIndex:
        entry = k.btck_chainstate_manager_get_block_tree_entry_by_hash(
            self._chainman, key
        )
        if not entry:
            raise KeyError(f"{key} not found")
        return BlockIndex._from_view(entry)


class BlockMap(MapBase):
    def __getitem__(self, key: BlockIndex) -> Block:
        entry = k.btck_block_read(self._chainman, key)
        if not entry:
            raise RuntimeError(f"Error reading Block for {key} from disk")
        return Block._from_handle(entry)


class BlockSpentOutputsMap(MapBase):
    def __getitem__(self, key: BlockIndex) -> BlockSpentOutputs:
        if key.height == 0:
            raise KeyError("Genesis block does not have BlockSpentOutputs data")

        entry = k.btck_block_spent_outputs_read(self._chainman, key)
        if not entry:
            raise RuntimeError(f"Error reading BlockSpentOutputs for {key} from disk")
        return BlockSpentOutputs._from_handle(entry)


class ChainstateManager(KernelOpaquePtr):
    def __init__(
        self,
        chain_man_opts: ChainstateManagerOptions,
    ):
        super().__init__(chain_man_opts)

    @property
    def block_indexes(self) -> BlockIndexMap:
        return BlockIndexMap(self)

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

    @property
    def blocks(self) -> BlockMap:
        return BlockMap(self)

    @property
    def block_spent_outputs(self) -> BlockSpentOutputsMap:
        return BlockSpentOutputsMap(self)
