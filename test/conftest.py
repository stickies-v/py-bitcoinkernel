import tempfile
from pathlib import Path

import pytest

import pbk


@pytest.fixture
def temp_dir():
    dir = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
    try:
        yield Path(dir.name)
    finally:
        dir.cleanup()


@pytest.fixture
def chainman_regtest(temp_dir):
    chain_man = pbk.load_chainman(temp_dir, pbk.ChainType.REGTEST)

    with (Path(__file__).parent / "data" / "regtest" / "blocks.txt").open("r") as file:
        for line in file.readlines():
            chain_man.process_block(pbk.Block(bytes.fromhex(line)), True)

    return chain_man
