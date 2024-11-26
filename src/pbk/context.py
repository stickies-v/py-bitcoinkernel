import typing

import pbk.capi.bindings as k
from pbk.capi import KernelOpaquePtr

if typing.TYPE_CHECKING:
    from pbk.chain import ChainParameters
    from pbk.notifications import Notifications
    from pbk.validation import ValidationInterface

class ContextOptions(KernelOpaquePtr):
    def set_chainparams(self, chain_parameters: "ChainParameters"):
        k.kernel_context_options_set_chainparams(
            self, chain_parameters)

    def set_notifications(self, notifications: "Notifications"):
        k.kernel_context_options_set_notifications(
            self, notifications)

class Context(KernelOpaquePtr):
    def __init__(self, options: ContextOptions):
        super().__init__(options)

    def interrupt(self) -> bool:
        return k.kernel_context_interrupt(self)

    def register_validation_interface(self, interface: "ValidationInterface"):
        k.kernel_validation_interface_register(self, interface)
