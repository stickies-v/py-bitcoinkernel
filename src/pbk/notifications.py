import pbk.capi.bindings as k
import pbk.util.callbacks
from pbk.capi import KernelOpaquePtr


class NotificationInterfaceCallbacks(k.kernel_NotificationInterfaceCallbacks):
    def __init__(self, user_data=None, **callbacks):
        super().__init__()
        pbk.util.callbacks.initialize_callbacks(self, user_data, **callbacks)


default_notification_callbacks = NotificationInterfaceCallbacks(
    user_data=None,
    block_tip=lambda user_data, state, index: print(
        f"block_tip: state: {state}, index: {index}"
    ),
    header_tip=lambda user_data, state, height, timestamp, presync: print(
        f"header_tip: state: {state}, height: {height}, timestamp: {timestamp}, presync: {presync}"
    ),
    progress=lambda user_data, title, progress_percent, resume_possible: print(
        f"progress: title: {title}, progress_percent: {progress_percent}, resume_possible: {resume_possible}"
    ),
    warning_set=lambda user_data, warning, message: print(
        f"warning_set: warning: {warning}, message: {message}"
    ),
    warning_unset=lambda user_data, warning: print(
        f"warning_unset: warning: {warning}"
    ),
    flush_error=lambda user_data, message: print(f"flush_error: message: {message}"),
    fatal_error=lambda user_data, message: print(f"flush_error: message: {message}"),
)


class Notifications(KernelOpaquePtr):
    def __init__(
        self, callbacks: NotificationInterfaceCallbacks = default_notification_callbacks
    ):
        super().__init__(callbacks)
