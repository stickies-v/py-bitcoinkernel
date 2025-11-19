from pathlib import Path

import pbk
import pytest
from pbk.util.exc import ProcessBlockException


def test_chain_type():
    for chain_type in pbk.ChainType:
        pbk.ChainParameters(chain_type)


def test_chainstate_manager_options(temp_dir: Path):
    opts = pbk.ContextOptions()
    context = pbk.Context(opts)

    # Test Context __repr__
    assert repr(context).startswith("<Context at 0x")
    assert repr(context).endswith(">")

    chain_man_opts = pbk.ChainstateManagerOptions(
        context, str(temp_dir), str(temp_dir / "blocks")
    )

    # Allowed combinations
    for block_tree, chainstate in [[True, True], [False, True], [False, False]]:
        assert chain_man_opts.set_wipe_dbs(block_tree, chainstate) == 0
    # Disallowed combinations
    for block_tree, chainstate in [[True, False]]:
        assert chain_man_opts.set_wipe_dbs(block_tree, chainstate) != 0

    # valid number
    for num_threads in [0, 1, 5]:
        chain_man_opts.set_worker_threads_num(num_threads)
        pbk.ChainstateManager(chain_man_opts)

    # invalid numbers are automatically clamped between 0-15
    for num_threads in [-10, -1, 100]:
        chain_man_opts.set_worker_threads_num(num_threads)
        pbk.ChainstateManager(chain_man_opts)

    chain_man_opts.update_block_tree_db_in_memory(True)
    chain_man_opts.update_chainstate_db_in_memory(True)
    pbk.ChainstateManager(chain_man_opts)


def test_chainstate_manager(chainman_regtest: pbk.ChainstateManager):
    chain_man = chainman_regtest
    chain = chain_man.get_active_chain()
    genesis = chain.block_tree_entries[0]

    assert chain_man.block_tree_entries[genesis.block_hash] == genesis
    assert chain_man.import_blocks([]) == 0  # TODO: implement actual test


def test_process_block(temp_dir: Path):
    chain_man = pbk.load_chainman(temp_dir, pbk.ChainType.REGTEST)

    blocks_path = Path(__file__).parent / "data" / "regtest" / "blocks.txt"
    with open(blocks_path, "r") as f:
        block_1 = pbk.Block(bytes.fromhex(f.readline()))

    # It should be a new block
    assert chain_man.process_block(block_1) is True

    # Process the same block again, not a new block anymore
    assert chain_man.process_block(block_1) is False

    # Create a corrupted block by modifying the raw bytes. Flip a bit in the merkle root
    corrupted_raw = bytearray(bytes(block_1))
    corrupted_raw[40] ^= 0xFF  # Flip bits in merkle root
    corrupted_block = pbk.Block(bytes(corrupted_raw))

    with pytest.raises(ProcessBlockException):
        chain_man.process_block(corrupted_block)


def test_chain(chainman_regtest: pbk.ChainstateManager):
    chain_man = chainman_regtest
    chain = chain_man.get_active_chain()

    assert chain.height == 206
    assert chain.height + 1 == len(chain.block_tree_entries)

    tip = chain.block_tree_entries[-1]
    assert tip.height == chain.height
    assert len(chain.block_tree_entries) == chain.height + 1
    previous = chain.block_tree_entries[tip.height - 1]
    assert isinstance(previous, pbk.BlockTreeEntry)
    assert previous.height == tip.height - 1

    # Test Chain __repr__
    assert repr(chain) == "<Chain height=206>"

    # Test ChainstateManager __repr__
    assert repr(chain_man).startswith("<ChainstateManager at 0x")
    assert repr(chain_man).endswith(">")


def test_read_block(chainman_regtest: pbk.ChainstateManager):
    chain_man = chainman_regtest
    chain = chain_man.get_active_chain()
    chain_tip = chain.block_tree_entries[-1]

    block_tip = chain_man.blocks[chain_tip]
    assert block_tip.block_hash == chain_tip.block_hash
    copied_block = pbk.Block(bytes(block_tip))
    assert copied_block.block_hash == block_tip.block_hash

    with pytest.raises(
        KeyError, match="Genesis block does not have BlockSpentOutputs data"
    ):
        chain_man.block_spent_outputs[chain.block_tree_entries[0]]
