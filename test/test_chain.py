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
        assert chain_man_opts.set_wipe_dbs(block_tree, chainstate)
    # Disallowed combinations
    for block_tree, chainstate in [[True, False]]:
        assert not chain_man_opts.set_wipe_dbs(block_tree, chainstate)

    # valid number
    for num_threads in [0, 1, 5]:
        chain_man_opts.set_worker_threads_num(num_threads)
        pbk.ChainstateManager(context, chain_man_opts)

    # invalid numbers are automatically clamped between 0-15
    for num_threads in [-10, -1, 100]:
        chain_man_opts.set_worker_threads_num(num_threads)
        pbk.ChainstateManager(context, chain_man_opts)


def test_chainstate_manager(chainman_regtest: pbk.ChainstateManager):
    chain_man = chainman_regtest

    genesis = chain_man.get_block_index_from_genesis()
    assert chain_man.get_block_index_from_height(0) == genesis
    assert chain_man.get_block_index_from_hash(genesis.block_hash) == genesis

    tip = chain_man.get_block_index_from_tip()
    assert not chain_man.get_next_block_index(tip)
    previous = chain_man.get_previous_block_index(tip)
    assert isinstance(previous, pbk.BlockIndex)
    assert previous.height == tip.height - 1
    assert chain_man.get_next_block_index(previous) == tip


def test_read_block(chainman_regtest: pbk.ChainstateManager):
    chain_man = chainman_regtest
    chain_tip = chain_man.get_block_index_from_tip()

    block_tip = chain_man.read_block_from_disk(chain_tip)
    assert block_tip.hash == chain_tip.block_hash
    copied_block = pbk.Block(block_tip.data)
    assert copied_block.hash == block_tip.hash

    genesis = chain_man.get_block_index_from_genesis()
    with pytest.raises(ValueError, match="Genesis block does not have undo data"):
        chain_man.read_block_undo_from_disk(genesis)


def test_block_index_generator(chainman_regtest: pbk.ChainstateManager):
    chain_man = chainman_regtest
    chain_tip = chain_man.get_block_index_from_tip()
    for i, idx in enumerate(pbk.block_index_generator(chain_man)):
        assert isinstance(idx, pbk.BlockIndex)
        assert idx.height == i
    assert idx == chain_tip

    idx_5 = chain_man.get_block_index_from_height(5)
    assert list(pbk.block_index_generator(chain_man, start=idx_5, end=5)) == [idx_5]
    idx_6 = chain_man.get_block_index_from_height(6)
    assert list(pbk.block_index_generator(chain_man, start=6, end=idx_5)) == [
        idx_6,
        idx_5,
    ]
    assert list(pbk.block_index_generator(chain_man, start=-1, end=-1)) == [chain_tip]

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
            list(pbk.block_index_generator(chain_man, start=start, end=end))
