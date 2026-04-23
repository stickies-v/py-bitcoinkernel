import ctypes
from collections.abc import Callable
from enum import IntEnum

import pbk.capi.bindings as k
import pbk.util.callbacks
from pbk.block import Block, BlockTreeEntry
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
    """

    _create_fn = k.btck_block_validation_state_create
    _destroy_fn = k.btck_block_validation_state_destroy

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


def _wrap_block_and_state(fn: Callable[..., None]) -> Callable[..., None]:
    def wrapper(
        user_data: ctypes.c_void_p,
        block_ptr: ctypes.c_void_p,
        state_ptr: ctypes.c_void_p,
    ) -> None:
        fn(
            user_data,
            Block._from_handle(block_ptr),
            BlockValidationState._from_view(state_ptr),
        )

    return wrapper


def _wrap_block_and_entry(fn: Callable[..., None]) -> Callable[..., None]:
    def wrapper(
        user_data: ctypes.c_void_p,
        block_ptr: ctypes.c_void_p,
        entry_ptr: ctypes.c_void_p,
    ) -> None:
        fn(
            user_data,
            Block._from_handle(block_ptr),
            BlockTreeEntry._from_view(entry_ptr),
        )

    return wrapper


_VALIDATION_CALLBACK_WRAPPERS = {
    "block_checked": _wrap_block_and_state,
    "pow_valid_block": _wrap_block_and_entry,
    "block_connected": _wrap_block_and_entry,
    "block_disconnected": _wrap_block_and_entry,
}


class ValidationInterfaceCallbacks(k.btck_ValidationInterfaceCallbacks):
    """Callbacks for receiving validation events.

    These callbacks allow monitoring of block validation progress and results.
    Callbacks are invoked synchronously during validation and will block further
    validation execution until they complete, so they should execute quickly.

    All callbacks are optional; only those passed as keyword arguments are
    registered, and any unspecified event is silently ignored.

    Available callbacks, each invoked with `(user_data, block, entry_or_state)`:
      - `block_checked(user_data, block: Block, state: BlockValidationState)`:
        a block has been fully validated. `state` is only valid for the duration
        of the callback — do not retain it.
      - `pow_valid_block(user_data, block: Block, entry: BlockTreeEntry)`:
        a block extends the header chain with valid PoW.
      - `block_connected(user_data, block: Block, entry: BlockTreeEntry)`:
        a valid block was connected to the best chain.
      - `block_disconnected(user_data, block: Block, entry: BlockTreeEntry)`:
        a block was disconnected during a reorg.

    `block` is owned by the callback; `entry` is a view into the kernel's
    block index and remains valid for the kernel's lifetime.

    Example:
        Register only `block_disconnected`:

        >>> cbs = ValidationInterfaceCallbacks(
        ...     block_disconnected=lambda user_data, block, entry: print(entry.height)
        ... )
    """

    def __init__(
        self,
        user_data: UserData | None = None,
        **callbacks: Callable[..., None],
    ):
        """Create validation interface callbacks.

        Args:
            user_data: Optional user-defined data passed to all callbacks.
            **callbacks: Callback functions for validation events, keyed by callback name
                         (e.g. ``block_disconnected=my_fn``). All are optional; omitted
                         callbacks are left unset.

        Raises:
            ValueError: If an unknown callback name is passed.
        """
        super().__init__()
        wrapped = {
            name: _VALIDATION_CALLBACK_WRAPPERS[name](fn)
            if name in _VALIDATION_CALLBACK_WRAPPERS
            else fn
            for name, fn in callbacks.items()
        }
        pbk.util.callbacks._initialize_callbacks(self, user_data, **wrapped)


default_validation_callbacks = ValidationInterfaceCallbacks(
    user_data=None,
    block_checked=lambda user_data, block, state: print(
        f"block_checked: block: {block}, state: {state}"
    ),
    pow_valid_block=lambda user_data, block, entry: print(
        f"pow_valid_block: block: {block}, entry: {entry}"
    ),
    block_connected=lambda user_data, block, entry: print(
        f"block_connected: block: {block}, entry: {entry}"
    ),
    block_disconnected=lambda user_data, block, entry: print(
        f"block_disconnected: block: {block}, entry: {entry}"
    ),
)
