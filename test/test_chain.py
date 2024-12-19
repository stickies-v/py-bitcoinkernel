from pathlib import Path


import pbk


def test_chainstate_manager_options(temp_dir: Path):
    opts = pbk.ContextOptions()
    context = pbk.Context(opts)
    block_man_opts = pbk.BlockManagerOptions(context, str(temp_dir / "blocks"))
    chain_man_opts = pbk.ChainstateManagerOptions(context, str(temp_dir))
    chain_load_opts = pbk.ChainstateLoadOptions()

    # valid number
    for num_threads in [0, 1, 5]:
        chain_man_opts.set_worker_threads_num(num_threads)
        pbk.ChainstateManager(context, chain_man_opts, block_man_opts, chain_load_opts)

    # invalid numbers are automatically clamped between 0-15
    for num_threads in [-10, -1, 100]:
        chain_man_opts.set_worker_threads_num(num_threads)
        pbk.ChainstateManager(context, chain_man_opts, block_man_opts, chain_load_opts)
