from collections.abc import Callable
from enum import IntEnum

import pbk.capi.bindings as k
import pbk.util.callbacks
from pbk.capi.base import KernelOpaquePtr
from pbk.util.type import UserData


class ValidationMode(IntEnum):
    """Result of validation processing.

    Indicates whether a data structure (such as a block) passed validation,
    failed validation, or encountered an error during processing.
    """

    VALID = 0  #: Validation succeeded
    INVALID = 1  #: Validation failed due to rule violations
    INTERNAL_ERROR = 2  #: An error occurred during validation processing


class BlockValidationResult(IntEnum):
    """Specific reason why a block failed validation.

    Provides detailed information about which validation rule was violated
    when a block is rejected. These results help diagnose why blocks fail
    to be accepted into the blockchain.
    """

    UNSET = 0  #: Initial value, block has not yet been rejected
    CONSENSUS = 1  #: Invalid by consensus rules (excluding specific reasons below)
    CACHED_INVALID = 2  #: Block was previously cached as invalid, reason not stored
    INVALID_HEADER = 3  #: Invalid proof of work or timestamp too old
    MUTATED = 4  #: Block data didn't match the data committed to by the PoW
    MISSING_PREV = 5  #: The previous block this builds on is not available
    INVALID_PREV = 6  #: A block this one builds on is invalid
    TIME_FUTURE = 7  #: Block timestamp was more than 2 hours in the future
    HEADER_LOW_WORK = 8  #: Block header may be on a too-little-work chain


class BlockValidationState(KernelOpaquePtr):
    """State of a block during validation.

    Contains information about whether validation was successful and, if not,
    which specific validation step failed. This state is provided to validation
    interface callbacks to communicate detailed validation results.

    Note:
        BlockValidationState instances cannot be directly constructed. They are
        obtained from validation interface callbacks.
    """

    @property
    def validation_mode(self) -> ValidationMode:
        """Overall validation result.

        Returns:
            Whether the block is valid, invalid, or encountered an error.
        """
        return k.btck_block_validation_state_get_validation_mode(self)

    @property
    def block_validation_result(self) -> BlockValidationResult:
        """Specific validation failure reason.

        Returns:
            The granular reason why validation failed, or UNSET if valid.
        """
        return k.btck_block_validation_state_get_block_validation_result(self)


class ValidationInterfaceCallbacks(k.btck_ValidationInterfaceCallbacks):
    """Callbacks for receiving validation events.

    These callbacks allow monitoring of block validation progress and results.
    Callbacks are invoked synchronously during validation and will block further
    validation execution until they complete, so they should execute quickly.

    Available callbacks:
      - `block_checked`: Called when a block has been fully validated with results
      - `pow_valid_block`: Called when a block extends the header chain with valid PoW
      - `block_connected`: Called when a valid block is connected to the best chain
      - `block_disconnected`: Called when a block is disconnected during a reorg
    """

    def __init__(
        self,
        user_data: UserData | None = None,
        **callbacks: Callable[..., None],
    ):
        """Create validation interface callbacks.

        Args:
            user_data: Optional user-defined data passed to all callbacks.
            **callbacks: Callback functions for validation events. The key is the name of the callback,
                         the value the callback function.
        """
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
