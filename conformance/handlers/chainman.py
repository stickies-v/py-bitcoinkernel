from pathlib import Path
import tempfile

from conformance.protocol import Parameters
import pbk


def btck_chainstate_manager_create(params: Parameters) -> pbk.ChainstateManager:
    temp_dir = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
    data_dir = Path(temp_dir.name)
    chainman = pbk.ChainstateManager(
        pbk.ChainstateManagerOptions(
            params["context"].value, str(data_dir), str(data_dir / "blocks")
        )
    )
    chainman._temp_dir = temp_dir  # ty: ignore[unresolved-attribute]
    return chainman


def btck_chainstate_manager_get_active_chain(params: Parameters) -> pbk.Chain:
    return params["chainstate_manager"].value.get_active_chain()


def btck_chainstate_manager_process_block(params: Parameters) -> dict[str, bool]:
    chainman: pbk.ChainstateManager = params["chainstate_manager"].value
    return {"new_block": chainman.process_block(params["block"].value)}


def btck_chainstate_manager_destroy(params: Parameters) -> None:
    params["chainstate_manager"].delete()
