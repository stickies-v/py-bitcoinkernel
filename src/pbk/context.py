import typing

import pbk.capi.bindings as k
from pbk.capi import KernelOpaquePtr

if typing.TYPE_CHECKING:
    from pbk.chain import ChainParameters
    from pbk.notifications import NotificationInterfaceCallbacks
    from pbk.validation import ValidationInterfaceCallbacks


class ContextOptions(KernelOpaquePtr):
    _create_fn = k.btck_context_options_create
    _destroy_fn = k.btck_context_options_destroy

    def set_chainparams(self, chain_parameters: "ChainParameters"):
        k.btck_context_options_set_chainparams(self, chain_parameters)

    def set_notifications(self, notifications: "NotificationInterfaceCallbacks"):
        k.btck_context_options_set_notifications(self, notifications)

    def set_validation_interface(
        self, interface_callbacks: "ValidationInterfaceCallbacks"
    ):
        k.btck_context_options_set_validation_interface(self, interface_callbacks)


class Context(KernelOpaquePtr):
    _create_fn = k.btck_context_create
    _destroy_fn = k.btck_context_destroy

    def __init__(self, options: ContextOptions):
        super().__init__(options)

    def interrupt(self) -> bool:
        return k.btck_context_interrupt(self)

    def __repr__(self) -> str:
        return f"<Context at {hex(id(self))}>"
