from pbk.block import Block, BlockHash, BlockTreeEntry, BlockSpentOutputs
from pbk.chain import (
    Chain,
    ChainParameters,
    ChainstateManager,
    ChainstateManagerOptions,
    ChainType,
)
from pbk.context import Context, ContextOptions
from pbk.log import (
    KernelLogViewer,
    LogCategory,
    LogLevel,
    LoggingConnection,
    LoggingOptions,
    enable_log_category,
    disable_log_category,
    logging_set_options,
    set_log_level_category,
)
from pbk.script import (
    ScriptPubkey,
    ScriptVerificationFlags,
    ScriptVerifyException,
    ScriptVerifyStatus,
)
from pbk.transaction import (
    Coin,
    Transaction,
    TransactionInput,
    TransactionOutput,
    TransactionOutPoint,
    TransactionSpentOutputs,
    Txid,
)
from pbk.validation import BlockValidationResult, BlockValidationState, ValidationMode

__all__ = [
    "BlockHash",
    "BlockTreeEntry",
    "Block",
    "BlockSpentOutputs",
    "BlockValidationResult",
    "BlockValidationState",
    "Chain",
    "ChainParameters",
    "ChainstateManager",
    "ChainstateManagerOptions",
    "ChainType",
    "Coin",
    "Context",
    "ContextOptions",
    "KernelLogViewer",
    "LogCategory",
    "LogLevel",
    "LoggingConnection",
    "LoggingOptions",
    "ScriptPubkey",
    "ScriptVerificationFlags",
    "ScriptVerifyException",
    "ScriptVerifyStatus",
    "Transaction",
    "TransactionInput",
    "TransactionOutput",
    "TransactionOutPoint",
    "TransactionSpentOutputs",
    "Txid",
    "ValidationMode",
    "disable_log_category",
    "enable_log_category",
    "logging_set_options",
    "set_log_level_category",
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
    chain_man = ChainstateManager(chain_man_opts)

    return chain_man
