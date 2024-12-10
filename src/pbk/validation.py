import pbk.capi.bindings as k
import pbk.util.callbacks
from pbk.capi import KernelOpaquePtr


class ValidationInterfaceCallbacks(k.kernel_ValidationInterfaceCallbacks):
    def __init__(self, user_data=None, **callbacks):
        super().__init__()
        pbk.util.callbacks.initialize_callbacks(self, user_data, **callbacks)


default_validation_callbacks = ValidationInterfaceCallbacks(
    user_data=None,
    block_checked=lambda user_data, block, state: print(
        f"block_checked: block: {block}, state: {state}"
    ),
)


class ValidationInterface(KernelOpaquePtr):
    def __init__(
        self, callbacks: ValidationInterfaceCallbacks = default_validation_callbacks
    ):
        super().__init__(callbacks)