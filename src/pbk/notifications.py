import ctypes

import pbk.capi.bindings as k
import pbk.util.callbacks


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
    progress=lambda user_data,
    title,
    title_len,
    progress_percent,
    resume_possible: print(
        f"progress: title: {ctypes.string_at(title, title_len).decode('utf-8')}, progress_percent: {progress_percent}, resume_possible: {resume_possible}"
    ),
    warning_set=lambda user_data, warning, message, message_len: print(
        f"warning_set: warning: {warning}, message: {ctypes.string_at(message, message_len).decode('utf-8')}"
    ),
    warning_unset=lambda user_data, warning: print(
        f"warning_unset: warning: {warning}"
    ),
    flush_error=lambda user_data, message, message_len: print(
        f"flush_error: message: {ctypes.string_at(message, message_len).decode('utf-8')}"
    ),
    fatal_error=lambda user_data, message, message_len: print(
        f"fatal_error: message: {ctypes.string_at(message, message_len).decode('utf-8')}"
    ),
)
