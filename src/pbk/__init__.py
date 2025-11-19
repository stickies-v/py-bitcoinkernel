from pbk.block import (
    Block,
    BlockHash,
    BlockTreeEntry,
    BlockSpentOutputs,
    TransactionSequence,
    TransactionSpentOutputsSequence,
)
from pbk.chain import (
    BlockMap,
    BlockSpentOutputsMap,
    BlockTreeEntryMap,
    BlockTreeEntrySequence,
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
    CoinSequence,
    Transaction,
    TransactionInput,
    TransactionInputSequence,
    TransactionOutput,
    TransactionOutputSequence,
    TransactionOutPoint,
    TransactionSpentOutputs,
    Txid,
)
from pbk.util.exc import KernelException, ProcessBlockException
from pbk.validation import (
    BlockValidationResult,
    BlockValidationState,
    ValidationMode,
    ValidationInterfaceCallbacks,
)

__all__ = [
    "BlockHash",
    "BlockSpentOutputsMap",
    "BlockTreeEntryMap",
    "BlockTreeEntry",
    "BlockTreeEntrySequence",
    "Block",
    "BlockMap",
    "BlockSpentOutputs",
    "BlockValidationResult",
    "BlockValidationState",
    "Chain",
    "ChainParameters",
    "ChainstateManager",
    "ChainstateManagerOptions",
    "ChainType",
    "Coin",
    "CoinSequence",
    "Context",
    "ContextOptions",
    "KernelException",
    "KernelLogViewer",
    "LogCategory",
    "LogLevel",
    "LoggingConnection",
    "LoggingOptions",
    "ProcessBlockException",
    "ScriptPubkey",
    "ScriptVerificationFlags",
    "ScriptVerifyException",
    "ScriptVerifyStatus",
    "Transaction",
    "TransactionInput",
    "TransactionInputSequence",
    "TransactionOutput",
    "TransactionOutputSequence",
    "TransactionSpentOutputsSequence",
    "TransactionOutPoint",
    "TransactionSequence",
    "TransactionSpentOutputs",
    "Txid",
    "ValidationMode",
    "ValidationInterfaceCallbacks",
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
