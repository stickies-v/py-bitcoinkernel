import ctypes
import typing
from enum import IntEnum
from pathlib import Path

import pbk.capi.bindings as k
from pbk.block import Block, BlockHash, BlockTreeEntry, BlockSpentOutputs
from pbk.capi import KernelOpaquePtr
from pbk.util.exc import ProcessBlockException
from pbk.util.sequence import LazySequence

if typing.TYPE_CHECKING:
    from pbk import BlockHash, Context


# TODO: add enum auto-generation or testing to ensure it remains in
# sync with bitcoinkernel.h
class ChainType(IntEnum):
    """Enumeration of supported Bitcoin network types."""

    MAINNET = 0  #: Main Bitcoin network
    TESTNET = 1  #: Test Bitcoin network
    TESTNET_4 = 2  #: Testnet4 Bitcoin network
    SIGNET = 3  #: Signet Bitcoin network
    REGTEST = 4  #: Regression test network


class ChainParameters(KernelOpaquePtr):
    """Chain parameters describing properties of a Bitcoin network.

    Chain parameters define network-specific constants and rules. These
    are typically passed to [context options][pbk.ContextOptions] when
    creating a kernel context.
    """

    _create_fn = k.btck_chain_parameters_create
    _destroy_fn = k.btck_chain_parameters_destroy

    def __init__(self, chain_type: ChainType):
        """Create chain parameters for a specific network type.

        Args:
            chain_type: The Bitcoin network type to configure.

        Raises:
            RuntimeError: If the C constructor fails (propagated from base class).
        """
        super().__init__(chain_type)


class ChainstateManagerOptions(KernelOpaquePtr):
    """Configuration options for creating a [chainstate manager][pbk.ChainstateManager].

    These options specify how a chainstate manager should be initialized. Options need to be
    configured before passing it to a chainstate manager constructor.

    !!! warning
        Once a chainstate manager is initialized, changes to its options object are no longer
        reflected on the chainstate manager itself.
    """

    _create_fn = k.btck_chainstate_manager_options_create
    _destroy_fn = k.btck_chainstate_manager_options_destroy

    def __init__(self, context: "Context", datadir: str, blocks_dir: str):
        """Create chainstate manager options.

        Args:
            context: The kernel context to associate with.
            datadir: Non-empty path to the directory containing chainstate data. The
                directory will be created if it doesn't exist.
            blocks_dir: Non-empty path to the directory containing block data. The
                directory will be created if it doesn't exist.

        Raises:
            RuntimeError: If the C constructor fails due to invalid paths or
                other errors (propagated from base class).
        """
        datadir_bytes = datadir.encode("utf-8")
        blocksdir_bytes = blocks_dir.encode("utf-8")
        super().__init__(
            context,
            datadir_bytes,
            len(datadir_bytes),
            blocksdir_bytes,
            len(blocksdir_bytes),
        )

    def set_wipe_dbs(self, wipe_block_tree_db: bool, wipe_chainstate_db: bool) -> int:
        """Configure the wiping of the block tree database and the chainstate database.

        !!! warning
            If `wipe_block_tree_db==True`, [pbk.ChainstateManager.__init__][] and [pbk.ChainstateManager.import_blocks][]
            **must** be called for the wiping to take effect.


        Args:
            wipe_block_tree_db: Whether to wipe the block tree database.
                Should only be True if `wipe_chainstate_db` is also True.
            wipe_chainstate_db: Whether to wipe the chainstate database.

        Returns:
            0 if the configuration was successful, 1 otherwise.
        """
        return k.btck_chainstate_manager_options_set_wipe_dbs(
            self, wipe_block_tree_db, wipe_chainstate_db
        )

    def set_worker_threads_num(self, worker_threads: int):
        """Set the number of worker threads for parallel validation.

        Args:
            worker_threads: Number of worker threads for the validation thread
                pool. When set to 0, no parallel verification is performed.
                The value is internally clamped between 0 and 15.
        """
        k.btck_chainstate_manager_options_set_worker_threads_num(self, worker_threads)

    def update_block_tree_db_in_memory(self, block_tree_db_in_memory: bool):
        """Configure whether to use an in-memory block tree database.

        When enabled, the block tree database is stored in memory instead
        of on disk. Useful for testing or temporary validation tasks.

        Args:
            block_tree_db_in_memory: True to use in-memory storage,
                False to use disk storage.
        """
        k.btck_chainstate_manager_options_update_block_tree_db_in_memory(
            self, int(block_tree_db_in_memory)
        )

    def update_chainstate_db_in_memory(self, chainstate_db_in_memory: bool):
        """Configure whether to use an in-memory chainstate database.

        When enabled, the UTXO set and chainstate are stored in memory
        instead of on disk. Useful for testing or temporary validation tasks.

        Args:
            chainstate_db_in_memory: True to use in-memory storage,
                False to use disk storage.
        """
        k.btck_chainstate_manager_options_update_chainstate_db_in_memory(
            self, int(chainstate_db_in_memory)
        )


class BlockTreeEntrySequence(LazySequence[BlockTreeEntry]):
    """Lazily-evaluated sequence of block tree entries in a chain.

    This sequence provides access to the chain's block tree entries indexed
    by height. It supports iteration, length queries, and membership testing.
    The sequence is a view into the chain and reflects the current state. Its
    members and length may change during its lifetime, for example when blocks
    are added to the chain, or when a reorg happens.

    !!! warning
        The chain must not be mutated while iterating over this sequence. For
        example, if a reorg happens while iterating, there is no guarantee that
        the results belong to the same chain.
    """

    def __init__(self, chain: "Chain"):
        """Create a sequence view of block tree entries.

        Args:
            chain: The chain object to create a sequence view for.
        """
        self._chain = chain

    def __len__(self) -> int:
        """The number of entries in the sequence."""
        return len(self._chain)

    def _get_item(self, index: int) -> BlockTreeEntry:
        """Get the block tree entry at the given height."""
        return BlockTreeEntry._from_view(k.btck_chain_get_by_height(self._chain, index))

    def __contains__(self, other: typing.Any):
        """Return True if `other` exists in the sequence."""
        if not isinstance(other, BlockTreeEntry):
            return False
        result = k.btck_chain_contains(self._chain, other)
        assert result in [0, 1]
        return bool(result)


class Chain(KernelOpaquePtr):
    """View of the currently active blockchain.

    This object represents the best-known chain and provides access to
    its block tree entries via height-based indexing. It is a dynamic view that always
    reflects the current active chain, but its contents may change when
    the chainstate manager processes new blocks or reorgs occur.

    Note:
        The chain is a view with lifetime dependent on the chainstate manager
        it was retrieved from. Data retrieved from the chain is only consistent
        until new blocks are processed in the chainstate manager.
    """

    @property
    def height(self) -> int:
        """Current height of the chain tip.

        Returns:
            Height of the chain tip. Genesis block is at height 0.
        """
        return k.btck_chain_get_height(self)

    def _get_by_height(self, height: int) -> BlockTreeEntry:
        """Get the block tree entry at the given height."""
        return BlockTreeEntry._from_view(k.btck_chain_get_by_height(self, height))

    @property
    def block_tree_entries(self) -> BlockTreeEntrySequence:
        """Sequence of all block tree entries in the chain.

        Returns:
            A lazy sequence supporting indexing and iteration over blocks
            in the chain by height.
        """
        return BlockTreeEntrySequence(self)

    def __len__(self) -> int:
        """Number of blocks in the chain."""
        return self.height + 1

    def __repr__(self) -> str:
        """Return a string representation of the chain."""
        return f"<Chain height={self.height}>"


class MapBase:
    """Base class for dictionary-like views into chainstate manager data.

    This class provides the foundation for map-like interfaces that
    retrieve blockchain data from the chainstate manager. Subclasses
    implement specific data access patterns.
    """

    def __init__(self, chainman: "ChainstateManager"):
        """Create a map view.

        Args:
            chainman: The chainstate manager to retrieve data from.
        """
        self._chainman = chainman


class BlockTreeEntryMap(MapBase):
    """Dictionary-like interface for retrieving block tree entries by hash.

    This map allows looking up block tree entries using their block hashes.
    It provides read-only dictionary access to the block index maintained
    by the chainstate manager.
    """

    def __getitem__(self, key: BlockHash) -> BlockTreeEntry:
        """Retrieve a block tree entry by its block hash.

        Args:
            key: The block hash to look up.

        Returns:
            The block tree entry corresponding to the hash.

        Raises:
            KeyError: If the block hash is not found in the block index.
        """
        entry = k.btck_chainstate_manager_get_block_tree_entry_by_hash(
            self._chainman, key
        )
        if not entry:
            raise KeyError(f"{key} not found")
        return BlockTreeEntry._from_view(entry)


class BlockMap(MapBase):
    """Dictionary-like interface for reading blocks from disk.

    This map reads blocks from disk using block tree entries as keys.
    """

    def __getitem__(self, key: BlockTreeEntry) -> Block:
        """Read a block from disk using its block tree entry.

        Args:
            key: The block tree entry identifying which block to read.

        Returns:
            The full block data read from disk.

        Raises:
            RuntimeError: If reading the block from disk fails.
        """
        entry = k.btck_block_read(self._chainman, key)
        if not entry:
            raise RuntimeError(f"Error reading Block for {key} from disk")
        return Block._from_handle(entry)


class BlockSpentOutputsMap(MapBase):
    """Dictionary-like interface for reading block spent outputs (undo data).

    This map reads spent output data (also known as undo data) from disk.
    """

    def __getitem__(self, key: BlockTreeEntry) -> BlockSpentOutputs:
        """Read block spent outputs from disk using a block tree entry.

        Args:
            key: The block tree entry identifying which block's spent outputs
                to read.

        Returns:
            The spent outputs data for the block.

        Raises:
            KeyError: If attempting to read spent outputs for the genesis block,
                which has no spent outputs.
            RuntimeError: If reading the spent outputs from disk fails.
        """
        if key.height == 0:
            raise KeyError("Genesis block does not have BlockSpentOutputs data")

        entry = k.btck_block_spent_outputs_read(self._chainman, key)
        if not entry:
            raise RuntimeError(f"Error reading BlockSpentOutputs for {key} from disk")
        return BlockSpentOutputs._from_handle(entry)


class ChainstateManager(KernelOpaquePtr):
    """Central manager for blockchain validation and data retrieval.

    The chainstate manager is the primary interface for validation tasks
    and accessing blockchain data. It maintains the block index, UTXO set,
    and active chain. This is a complex internal data structure that will
    expose more functionality over time.

    The chainstate manager can be safely used from multiple threads.
    """

    _create_fn = k.btck_chainstate_manager_create
    _destroy_fn = k.btck_chainstate_manager_destroy

    def __init__(
        self,
        chain_man_opts: ChainstateManagerOptions,
    ):
        """Create a chainstate manager.

        !!! info
            If wiping options were [set][pbk.ChainstateManagerOptions.set_wipe_dbs] to
            `(wipe_block_tree_db==False, wipe_chainstate_db==True)`, the chainstate database will be
            rebuilt during initialization. This may take a long time.

        !!! info
            `bitcoinkernel` requires exclusive access to its data directories. The construction
            of a chainstate manager will fail if another process (e.g. Bitcoin Core) is currently
            using them.

        Args:
            chain_man_opts: Configuration options specifying data directories
                and other initialization parameters.

        Raises:
            TypeError: If instantiation is not supported (propagated from base class).
            RuntimeError: If creation fails due to invalid options, corrupted
                databases, or other errors (propagated from base class).
        """
        super().__init__(chain_man_opts)

    @property
    def block_tree_entries(self) -> BlockTreeEntryMap:
        """Dictionary-like interface for looking up block tree entries by hash.

        Returns:
            A map that retrieves block tree entries using block hashes as keys.
        """
        return BlockTreeEntryMap(self)

    def get_active_chain(self) -> Chain:
        """Get the currently active best-known blockchain.

        Returns a view of the active chain that always reflects the current
        best chain. Note that the chain's contents may change as new blocks
        are processed or as a reorg occurs.

        Returns:
            The active chain view.
        """
        return Chain._from_view(k.btck_chainstate_manager_get_active_chain(self))

    def import_blocks(self, paths: typing.List[Path]) -> bool:
        """Import blocks from block files.

        Args:
            paths: List of filesystem paths to block files to import.

        Returns:
            True if the import completed successfully, False otherwise.
        """
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

    def process_block(self, block: Block) -> bool:
        """Process and validate the passed in block with the chainstate manager.

        Processing first does checks on the block, and if these passed, saves it to disk.
        It then validates the block against the utxo set. If it is valid, the chain is
        extended with it.

        Args:
            block: The block to process.

        Returns:
            True if the block was not processed and saved to disk before, False otherwise.

        Raises:
            ProcessBlockException: If processing the block failed. Duplicate blocks do not throw.
        """
        is_new_block = ctypes.c_int()
        result = k.btck_chainstate_manager_process_block(
            self, block, ctypes.pointer(is_new_block)
        )
        if result != 0:
            raise ProcessBlockException(result)
        assert is_new_block.value in [0, 1]
        return bool(is_new_block.value)

    @property
    def blocks(self) -> BlockMap:
        """Dictionary-like interface for reading blocks from disk.

        Returns:
            A map that reads full block data using block tree entries as keys.
        """
        return BlockMap(self)

    @property
    def block_spent_outputs(self) -> BlockSpentOutputsMap:
        """Dictionary-like interface for reading block spent outputs (undo data).

        Returns:
            A map that reads spent output data using block tree entries as keys.
        """
        return BlockSpentOutputsMap(self)

    def __repr__(self) -> str:
        """Return a string representation of the chainstate manager."""
        return f"<ChainstateManager at {hex(id(self))}>"
