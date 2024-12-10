from pbk.block import Block, BlockHash, BlockIndex, BlockUndo
from pbk.chain import (
    BlockManagerOptions,
    ChainParameters,
    ChainstateLoadOptions,
    ChainstateManager,
    ChainstateManagerOptions,
    ChainType,
    block_index_generator,
)
from pbk.context import Context, ContextOptions
from pbk.log import LogCategory, LoggingConnection, LoggingOptions
from pbk.notifications import Notifications
from pbk.script import (
    ScriptPubkey,
    ScriptFlags,
    ScriptVerifyException,
    ScriptVerifyStatus,
    verify_script,
)
from pbk.transaction import Transaction, TransactionOutput, TransactionUndo
from pbk.validation import ValidationInterface

__all__ = [
    "Block",
    "BlockHash",
    "BlockIndex",
    "BlockUndo",
    "BlockManagerOptions",
    "ChainParameters",
    "ChainstateLoadOptions",
    "ChainstateManager",
    "ChainstateManagerOptions",
    "ChainType",
    "block_index_generator",
    "Context",
    "ContextOptions",
    "LogCategory",
    "LoggingConnection",
    "LoggingOptions",
    "Notifications",
    "ScriptPubkey",
    "ScriptFlags",
    "ScriptVerifyException",
    "ScriptVerifyStatus",
    "verify_script",
    "Transaction",
    "TransactionOutput",
    "TransactionUndo",
    "ValidationInterface",
]

from pathlib import Path


def make_context(chain_type: ChainType = ChainType.REGTEST) -> Context:
    chain_params = ChainParameters(chain_type)
    opts = ContextOptions()
    opts.set_chainparams(chain_params)
    return Context(opts)


def load_chainman(
    datadir: Path, chain_type: ChainType = ChainType.REGTEST
) -> ChainstateManager:
    context = make_context(chain_type)
    blocksdir = datadir / "blocks"

    block_man_opts = BlockManagerOptions(context, str(blocksdir.absolute()))
    chain_man_opts = ChainstateManagerOptions(context, str(datadir.absolute()))
    chain_man = ChainstateManager(context, chain_man_opts, block_man_opts)
    chain_load_opts = ChainstateLoadOptions()
    chain_man.load_chainstate(chain_load_opts)

    return chain_man
