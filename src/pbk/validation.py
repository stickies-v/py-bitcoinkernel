from enum import IntEnum

import pbk.capi.bindings as k
from pbk.capi import KernelOpaquePtr


class ValidationMode(IntEnum):
    """Result of validation processing.

    Indicates whether a data structure (such as a block) passed validation,
    failed validation, or encountered an error during processing.
    """

    VALID = 0
    """Validation succeeded"""

    INVALID = 1
    """Validation failed due to rule violations"""

    INTERNAL_ERROR = 2
    """An error occurred during validation processing"""


class BlockValidationResult(IntEnum):
    """Specific reason why a block failed validation.

    Provides detailed information about which validation rule was violated
    when a block is rejected. These results help diagnose why blocks fail
    to be accepted into the blockchain.
    """

    UNSET = 0
    """Initial value. Block has not yet been rejected"""

    CONSENSUS = 1
    """Invalid by consensus rules (excluding any below reasons)"""

    CACHED_INVALID = 2
    """This block was cached as being invalid and we didn't store the reason why"""

    INVALID_HEADER = 3
    """Invalid proof of work or time too old"""

    MUTATED = 4
    """The block's data didn't match the data committed to by the PoW"""

    MISSING_PREV = 5
    """We don't have the previous block the checked one is built on"""

    INVALID_PREV = 6
    """A block this one builds on is invalid"""

    TIME_FUTURE = 7
    """Block timestamp was > 2 hours in the future (or our clock is bad)"""

    HEADER_LOW_WORK = 8
    """The block header may be on a too-little-work chain"""


class BlockValidationState(KernelOpaquePtr):
    """State of a block during validation.

    Contains information about whether validation was successful and, if not,
    which specific validation step failed. This state is provided to validation
    interface callbacks to communicate detailed validation results.
    """

    _create_fn = k.btck_block_validation_state_create
    _destroy_fn = k.btck_block_validation_state_destroy
    _copy_fn = k.btck_block_validation_state_copy

    def __init__(self):
        """Create a block validation state."""
        super().__init__()

    @property
    def validation_mode(self) -> ValidationMode:
        """Overall validation result.

        Returns:
            Whether the block is valid, invalid, or encountered an error.
        """
        return ValidationMode(k.btck_block_validation_state_get_validation_mode(self))

    @property
    def block_validation_result(self) -> BlockValidationResult:
        """Specific validation failure reason.

        Returns:
            The granular reason why validation failed, or UNSET if valid.
        """
        return BlockValidationResult(
            k.btck_block_validation_state_get_block_validation_result(self)
        )

    def __repr__(self) -> str:
        """Return a string representation of the block validation state."""
        return f"<BlockValidationState mode={self.validation_mode.name} result={self.block_validation_result.name}>"
