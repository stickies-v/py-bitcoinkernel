import pbk


def test_validation_state() -> None:
    state = pbk.BlockValidationState()
    assert state.block_validation_result == pbk.BlockValidationResult.UNSET
    assert state.validation_mode == pbk.ValidationMode.VALID
