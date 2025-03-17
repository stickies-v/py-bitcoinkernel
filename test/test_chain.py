from pathlib import Path


import pbk


def test_chainstate_manager_options(temp_dir: Path):
    opts = pbk.ContextOptions()
    context = pbk.Context(opts)
    chain_man_opts = pbk.ChainstateManagerOptions(
        context, str(temp_dir), str(temp_dir / "blocks")
    )

    assert chain_man_opts.set_wipe_dbs(wipe_block_tree_db=True, wipe_chainstate_db=True)
    assert chain_man_opts.set_wipe_dbs(
        wipe_block_tree_db=False, wipe_chainstate_db=True
    )
    assert chain_man_opts.set_wipe_dbs(
        wipe_block_tree_db=False, wipe_chainstate_db=False
    )
    assert not chain_man_opts.set_wipe_dbs(
        wipe_block_tree_db=True, wipe_chainstate_db=False
    )

    # valid number
    for num_threads in [0, 1, 5]:
        chain_man_opts.set_worker_threads_num(num_threads)
        pbk.ChainstateManager(context, chain_man_opts)

    # invalid numbers are automatically clamped between 0-15
    for num_threads in [-10, -1, 100]:
        chain_man_opts.set_worker_threads_num(num_threads)
        pbk.ChainstateManager(context, chain_man_opts)
