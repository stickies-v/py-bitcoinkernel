from collections.abc import Callable
from pathlib import Path

import pbk


def test_chain_types() -> None:
    options = pbk.ContextOptions()
    for chain_type in pbk.ChainType:
        options.set_chainparams(pbk.ChainParameters(chain_type))
        context = pbk.Context(options)
        assert context is not None


def _build_chainman_with_inline_callback(
    temp_dir: Path, callback: Callable[..., None]
) -> pbk.ChainstateManager:
    opts = pbk.ContextOptions()
    opts.set_chainparams(pbk.ChainParameters(pbk.ChainType.REGTEST))
    opts.set_validation_interface(
        pbk.ValidationInterfaceCallbacks(block_connected=callback)
    )
    context = pbk.Context(opts)
    blocks_dir = temp_dir / "blocks"
    cm_opts = pbk.ChainstateManagerOptions(
        context, str(temp_dir.absolute()), str(blocks_dir.absolute())
    )
    return pbk.ChainstateManager(cm_opts)


def test_chainman_keeps_validation_callbacks_alive(temp_dir: Path) -> None:
    # Inline-constructed callbacks must survive past construction: if the
    # Python ContextOptions/Context/ChainstateManager don't keep them
    # referenced, the ctypes trampolines get freed and process_block would
    # use-after-free when the kernel invokes the stored C pointers.
    call_count = [0]
    cm = _build_chainman_with_inline_callback(
        temp_dir,
        lambda u, b, e: call_count.__setitem__(0, call_count[0] + 1),
    )
    blocks_file = Path(__file__).parent / "data" / "regtest" / "blocks.txt"
    with blocks_file.open() as f:
        block = pbk.Block(bytes.fromhex(f.readline().strip()))
    assert cm.process_block(block)
    assert call_count[0] > 0
