from pathlib import Path
import tempfile

from conformance.protocol import Parameters
import pbk


def btck_chainstate_manager_create(params: Parameters) -> pbk.ChainstateManager:
    context = params["context"].value
    temp_dir = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
    data_dir = Path(temp_dir.name)
    blocks_dir = data_dir / "blocks"
    opts = pbk.ChainstateManagerOptions(
        context, str(data_dir.absolute()), str(blocks_dir.absolute())
    )
    opts._temp_dir = temp_dir  # ensure temp_dir lifetime
    return pbk.ChainstateManager(opts)


def btck_chainstate_manager_get_active_chain(params: Parameters) -> pbk.Chain:
    chainman: pbk.ChainstateManager = params["chainstate_manager"].value
    return chainman.get_active_chain()


def btck_chainstate_manager_process_block(params: Parameters) -> dict[str, bool]:
    chainman: pbk.ChainstateManager = params["chainstate_manager"].value
    block: pbk.Block = params["block"].value

    return {"new_block": chainman.process_block(block)}


def btck_chainstate_manager_destroy(params: Parameters) -> None:
    params["chainstate_manager"].delete()
