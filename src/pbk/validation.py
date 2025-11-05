from enum import IntEnum
from pbk.capi.base import KernelOpaquePtr
import pbk.capi.bindings as k
import pbk.util.callbacks


class ValidationMode(IntEnum):
    VALID = 0  # btck_ValidationMode_VALID
    INVALID = 1  # btck_ValidationMode_INVALID
    INTERNAL_ERROR = 2  # btck_ValidationMode_INTERNAL_ERROR


class BlockValidationResult(IntEnum):
    UNSET = 0  # btck_BlockValidationResult_UNSET: initial value. Block has not yet been rejected
    CONSENSUS = 1  # btck_BlockValidationResult_CONSENSUS: invalid by consensus rules (excluding any below reasons)
    CACHED_INVALID = 2  # btck_BlockValidationResult_CACHED_INVALID: this block was cached as being invalid and we didn't store the reason why
    INVALID_HEADER = 3  # btck_BlockValidationResult_INVALID_HEADER: invalid proof of work or time too old
    MUTATED = 4  # btck_BlockValidationResult_MUTATED: the block's data didn't match the data committed to by the PoW
    MISSING_PREV = 5  # btck_BlockValidationResult_MISSING_PREV: We don't have the previous block the checked one is built on
    INVALID_PREV = 6  # btck_BlockValidationResult_INVALID_PREV: A block this one builds on is invalid
    TIME_FUTURE = 7  # btck_BlockValidationResult_TIME_FUTURE: block timestamp was > 2 hours in the future (or our clock is bad)
    HEADER_LOW_WORK = 8  # btck_BlockValidationResult_HEADER_LOW_WORK: the block header may be on a too-little-work chain


class BlockValidationState(KernelOpaquePtr):
    def __init__(self, *args, **kwargs):
        raise NotImplementedError()

    @property
    def validation_mode(self) -> ValidationMode:
        return k.btck_block_validation_state_get_validation_mode(self)

    @property
    def block_validation_result(self) -> BlockValidationResult:
        return k.btck_block_validation_state_get_block_validation_result(self)


class ValidationInterfaceCallbacks(k.btck_ValidationInterfaceCallbacks):
    def __init__(self, user_data=None, **callbacks):
        super().__init__()
        pbk.util.callbacks._initialize_callbacks(self, user_data, **callbacks)


default_validation_callbacks = ValidationInterfaceCallbacks(
    user_data=None,
    block_checked=lambda user_data, block, state: print(
        f"block_checked: block: {block}, state: {state}"
    ),
    pow_valid_block=lambda user_data, block, state: print(
        f"pow_valid_block: block: {block}, state: {state}"
    ),
    block_connected=lambda user_data, block, state: print(
        f"block_connected: block: {block}, state: {state}"
    ),
    block_disconnected=lambda user_data, block, state: print(
        f"block_disconnected: block: {block}, state: {state}"
    ),
)
