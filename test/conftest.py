import tempfile
from pathlib import Path

import pytest

import pbk
from pbk import chain


@pytest.fixture
def temp_dir():
    # Create TemporaryDirectory
    dir = tempfile.TemporaryDirectory()
    try:
        yield Path(dir.name)
    finally:
        dir.cleanup()

def make_context(chain_type: pbk.ChainType = pbk.ChainType.REGTEST) -> pbk.Context:
    # log = pbk.LoggingConnection()
    
    chain_params = pbk.ChainParameters(chain_type)
    # notifications = pbk.Notifications()
    opts = pbk.ContextOptions()
    opts.set_chainparams(chain_params)
    # opts.set_notifications(notifications)
    return pbk.Context(opts)

def make_chainman(datadir: Path, chain_type: pbk.ChainType = pbk.ChainType.REGTEST) -> pbk.ChainstateManager:
    context = make_context(chain_type)
    blocksdir = datadir / "blocks"
    # validation_interface = pbk.ValidationInterface()
    # context.register_validation_interface(validation_interface)

    block_man_opts = pbk.BlockManagerOptions(context, str(blocksdir.absolute()))
    chain_man_opts = pbk.ChainstateManagerOptions(context, str(datadir.absolute()))
    chain_man = pbk.ChainstateManager(context, chain_man_opts, block_man_opts)
    chain_load_opts = pbk.ChainstateLoadOptions()
    chain_load_opts.set_wipe_block_tree_db(False)
    chain_load_opts.set_wipe_chainstate_db(False)
    chain_man.load_chainstate(chain_load_opts)

    with (Path(__file__).parent / "data" / "regtest" / "blocks.txt").open('r') as file:
        for line in file.readlines():
            chain_man.process_block(pbk.Block(bytes.fromhex(line)), True)

    return chain_man

@pytest.fixture
def chainman_regtest(temp_dir):
    return make_chainman(temp_dir, pbk.ChainType.REGTEST)
