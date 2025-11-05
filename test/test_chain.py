from pathlib import Path

import pbk
import pytest


def test_chain_type():
    for chain_type in pbk.ChainType:
        pbk.ChainParameters(chain_type)


def test_chainstate_manager_options(temp_dir: Path):
    opts = pbk.ContextOptions()
    context = pbk.Context(opts)
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

    genesis = chain.get_genesis()
    assert chain.get_by_height(0) == genesis
    assert chain_man.get_block_index_from_hash(genesis.block_hash) == genesis

    tip = chain.get_tip()
    assert tip.height == chain.height
    previous = chain.get_by_height(tip.height - 1)
    assert isinstance(previous, pbk.BlockIndex)
    assert previous.height == tip.height - 1
    assert chain.get_by_height(previous.height + 1) == tip

    assert chain_man.import_blocks([]) == 0


def test_read_block(chainman_regtest: pbk.ChainstateManager):
    chain_man = chainman_regtest
    chain = chain_man.get_active_chain()
    chain_tip = chain.get_tip()

    block_tip = chain_man.read_block_from_disk(chain_tip)
    assert block_tip.hash == chain_tip.block_hash
    copied_block = pbk.Block(block_tip.data)
    assert copied_block.hash == block_tip.hash

    with pytest.raises(ValueError, match="Genesis block does not have undo data"):
        chain_man.read_block_undo_from_disk(chain.get_genesis())


def test_block_index_generator(chainman_regtest: pbk.ChainstateManager):
    chain = chainman_regtest.get_active_chain()
    chain_tip = chain.get_tip()
    for i, idx in enumerate(pbk.block_index_generator(chain)):
        assert isinstance(idx, pbk.BlockIndex)
        assert idx.height == i
    assert idx == chain_tip

    idx_5 = chain.get_by_height(5)
    assert list(pbk.block_index_generator(chain, start=idx_5, end=5)) == [idx_5]
    idx_6 = chain.get_by_height(6)
    assert list(pbk.block_index_generator(chain, start=6, end=idx_5)) == [
        idx_6,
        idx_5,
    ]
    assert list(pbk.block_index_generator(chain, start=-1, end=-1)) == [chain_tip]

    # Test invalid bounds
    invalid_bounds = [
        (None, chain_tip.height + 1),
        (None, -(chain_tip.height + 2)),
        (-(chain_tip.height + 2), -(chain_tip.height + 2)),
        (-(chain_tip.height + 2), None),
        (chain_tip.height + 1, None),
    ]
    for start, end in invalid_bounds:
        with pytest.raises(IndexError, match="is out of bounds"):
            list(pbk.block_index_generator(chain, start=start, end=end))
