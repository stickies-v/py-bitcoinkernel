import ctypes
from collections.abc import Callable

import pbk.capi.bindings as k
import pbk.util.callbacks


class NotificationInterfaceCallbacks(k.btck_NotificationInterfaceCallbacks):
    """Callbacks for receiving kernel notification events.

    All callbacks are optional; only those passed as keyword arguments are
    registered, and any unspecified event is silently ignored.
    """

    def __init__(self, **callbacks: Callable[..., None]):
        """Create notification interface callbacks.

        Args:
            **callbacks: Callback functions for notification events, keyed by callback name.
                         All are optional; omitted callbacks are left unset.

        Raises:
            ValueError: If an unknown callback name is passed.
        """
        super().__init__()
        pbk.util.callbacks._initialize_callbacks(self, **callbacks)


default_notification_callbacks = NotificationInterfaceCallbacks(
    block_tip=lambda state, index, verification_progress: print(
        f"block_tip: state: {state}, index: {index}, verification_progress: {verification_progress}"
    ),
    header_tip=lambda state, height, timestamp, presync: print(
        f"header_tip: state: {state}, height: {height}, timestamp: {timestamp}, presync: {presync}"
    ),
    progress=lambda title, title_len, progress_percent, resume_possible: print(
        f"progress: title: {ctypes.string_at(title, title_len).decode('utf-8')}, progress_percent: {progress_percent}, resume_possible: {resume_possible}"
    ),
    warning_set=lambda warning, message, message_len: print(
        f"warning_set: warning: {warning}, message: {ctypes.string_at(message, message_len).decode('utf-8')}"
    ),
    warning_unset=lambda warning: print(f"warning_unset: warning: {warning}"),
    flush_error=lambda message, message_len: print(
        f"flush_error: message: {ctypes.string_at(message, message_len).decode('utf-8')}"
    ),
    fatal_error=lambda message, message_len: print(
        f"fatal_error: message: {ctypes.string_at(message, message_len).decode('utf-8')}"
    ),
)
