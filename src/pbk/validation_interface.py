import ctypes
from collections.abc import Callable

import pbk.capi.bindings as k
import pbk.util.callbacks
from pbk.block import (
    Block,
    BlockTreeEntry,
    BlockValidationState,
)


def _wrap_block_and_state(fn: Callable[..., None]) -> Callable[..., None]:
    def wrapper(block_ptr: ctypes.c_void_p, state_ptr: ctypes.c_void_p) -> None:
        fn(Block._from_handle(block_ptr), BlockValidationState._from_view(state_ptr))

    return wrapper


def _wrap_block_and_entry(fn: Callable[..., None]) -> Callable[..., None]:
    def wrapper(block_ptr: ctypes.c_void_p, entry_ptr: ctypes.c_void_p) -> None:
        fn(Block._from_handle(block_ptr), BlockTreeEntry._from_view(entry_ptr))

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

    Available callbacks, each invoked with `(block, entry_or_state)`:
      - `block_checked(block: Block, state: BlockValidationState)`:
        a block has been fully validated. `state` is only valid for the duration
        of the callback — do not retain it.
      - `pow_valid_block(block: Block, entry: BlockTreeEntry)`:
        a block extends the header chain with valid PoW.
      - `block_connected(block: Block, entry: BlockTreeEntry)`:
        a valid block was connected to the best chain.
      - `block_disconnected(block: Block, entry: BlockTreeEntry)`:
        a block was disconnected during a reorg.

    `block` is owned by the callback; `entry` is a view into the kernel's
    block index and remains valid for the kernel's lifetime.

    Example:
        Register only `block_disconnected`:

        >>> cbs = ValidationInterfaceCallbacks(
        ...     block_disconnected=lambda block, entry: print(entry.height)
        ... )
    """

    def __init__(
        self,
        **callbacks: Callable[..., None],
    ):
        """Create validation interface callbacks.

        Args:
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
        pbk.util.callbacks._initialize_callbacks(self, **wrapped)


default_validation_callbacks = ValidationInterfaceCallbacks(
    block_checked=lambda block, state: print(
        f"block_checked: block: {block}, state: {state}"
    ),
    pow_valid_block=lambda block, entry: print(
        f"pow_valid_block: block: {block}, entry: {entry}"
    ),
    block_connected=lambda block, entry: print(
        f"block_connected: block: {block}, entry: {entry}"
    ),
    block_disconnected=lambda block, entry: print(
        f"block_disconnected: block: {block}, entry: {entry}"
    ),
)
