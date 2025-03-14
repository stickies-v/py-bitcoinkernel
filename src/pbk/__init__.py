from pbk.block import Block, BlockHash, BlockIndex, BlockUndo
from pbk.chain import (
    ChainParameters,
    ChainstateManager,
    ChainstateManagerOptions,
    ChainType,
    block_index_generator,
)
from pbk.context import Context, ContextOptions
from pbk.log import (
    KernelLogViewer,
    LogCategory,
    LogLevel,
    LoggingConnection,
    LoggingOptions,
    add_log_level_category,
    enable_log_category,
    disable_log_category,
)
from pbk.script import (
    ScriptPubkey,
    ScriptFlags,
    ScriptVerifyException,
    ScriptVerifyStatus,
    verify_script,
)
from pbk.transaction import Transaction, TransactionOutput, TransactionUndo

__all__ = [
    "BlockHash",
    "BlockIndex",
    "Block",
    "BlockUndo",
    "ChainParameters",
    "ChainstateManager",
    "ChainstateManagerOptions",
    "ChainType",
    "Context",
    "ContextOptions",
    "KernelLogViewer",
    "LogCategory",
    "LogLevel",
    "LoggingConnection",
    "LoggingOptions",
    "ScriptFlags",
    "ScriptPubkey",
    "ScriptVerifyException",
    "ScriptVerifyStatus",
    "Transaction",
    "TransactionOutput",
    "TransactionUndo",
    "add_log_level_category",
    "block_index_generator",
    "disable_log_category",
    "enable_log_category",
    "verify_script",
]

from pathlib import Path


def make_context(chain_type: ChainType = ChainType.REGTEST) -> Context:
    chain_params = ChainParameters(chain_type)
    opts = ContextOptions()
    opts.set_chainparams(chain_params)
    return Context(opts)


def load_chainman(
    datadir: Path | str, chain_type: ChainType = ChainType.REGTEST
) -> ChainstateManager:
    """
    Load and initialize a `ChainstateManager` object, loading its
    chainstate from disk.

    **IMPORTANT**: `py-bitcoinkernel` requires exclusive access to the
    data directory. Sharing a data directory with Bitcoin Core will ONLY
    work when only one of both programs is running at a time.

    @param datadir: The path of the data directory. If the directory
        contains an existing `blocks/` and `chainstate/` directory
        created by Bitoin Core, it will be used to load the chainstate.
        Otherwise, a new chainstate will be created.
    @param chain_type: The type of chain to load.
    @return: A `ChainstateManager` object.
    """
    datadir = Path(datadir)
    context = make_context(chain_type)
    blocksdir = datadir / "blocks"

    chain_man_opts = ChainstateManagerOptions(
        context, str(datadir.absolute()), str(blocksdir.absolute())
    )
    chain_man = ChainstateManager(context, chain_man_opts)

    return chain_man
