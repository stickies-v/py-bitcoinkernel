from pathlib import Path

import pytest

import pbk


def test_chainstate_manager_options(temp_dir: Path):
    opts = pbk.ContextOptions()
    context = pbk.Context(opts)
    block_man_opts = pbk.BlockManagerOptions(context, str(temp_dir / "blocks"))
    chain_man_opts = pbk.ChainstateManagerOptions(context, str(temp_dir))

    # valid number
    for num_threads in [0, 1, 5, 100]:
        chain_man_opts.set_worker_threads_num(num_threads)
        pbk.ChainstateManager(context, chain_man_opts, block_man_opts)

    # invalid number
    for num_threads in [
        -1,
    ]:
        chain_man_opts.set_worker_threads_num(num_threads)
        with pytest.raises(RuntimeError):
            pbk.ChainstateManager(context, chain_man_opts, block_man_opts)
