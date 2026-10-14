from pathlib import Path

import pytest

import pbk

# Mainnet block 1.
BLOCK_1_HEADER_HEX = "010000006fe28c0ab6f1b372c1a6a246ae63f74f931e8365e15a089c68d6190000000000982051fd1e4ba744bbbe680e1fee14677ba1a3c3540bf7b1cdb606e857233e0e61bc6649ffff001d01e36299"


def test_set_mock_time(temp_dir: Path) -> None:
    chain_man = pbk.load_chainman(temp_dir, pbk.ChainType.MAINNET)
    header = pbk.BlockHeader(bytes.fromhex(BLOCK_1_HEADER_HEX))

    # The kernel clock is only observable through validation: at mock time 1,
    # every header is in the future.
    pbk.set_mock_time(1)
    try:
        state = chain_man.process_block_header(header)
    finally:
        pbk.set_mock_time(0)
    assert state.validation_mode == pbk.ValidationMode.INVALID
    assert state.block_validation_result == pbk.BlockValidationResult.TIME_FUTURE

    # 0 restores the system clock.
    state = chain_man.process_block_header(header)
    assert state.validation_mode == pbk.ValidationMode.VALID

    for invalid in [-1, 2**32]:
        with pytest.raises(ValueError, match="outside"):
            pbk.set_mock_time(invalid)
