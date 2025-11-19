import typing

import pbk.capi.bindings as k
from pbk.capi import KernelOpaquePtr

if typing.TYPE_CHECKING:
    from pbk.chain import ChainParameters
    from pbk.notifications import NotificationInterfaceCallbacks
    from pbk.validation import ValidationInterfaceCallbacks


class ContextOptions(KernelOpaquePtr):
    """Options for creating a new kernel context.

    Once a kernel context has been created from this options object, it may be destroyed. Changes
    made to the options after the kernel context has been created will not be reflected on the
    kernel context.
    """

    _create_fn = k.btck_context_options_create
    _destroy_fn = k.btck_context_options_destroy

    def __init__(self):
        """Create context options."""
        super().__init__()

    def set_chainparams(self, chain_parameters: "ChainParameters"):
        """Sets the chain parameters for the context options.

        Args:
            chain_parameters: Chain parameters to set.
        """
        k.btck_context_options_set_chainparams(self, chain_parameters)

    def set_notifications(self, notifications: "NotificationInterfaceCallbacks"):
        """Sets the kernel notifications for the context options.

        Args:
            notifications: Notification callbacks to set.
        """
        k.btck_context_options_set_notifications(self, notifications)

    def set_validation_interface(
        self, interface_callbacks: "ValidationInterfaceCallbacks"
    ):
        """Sets the validation interface callbacks for the context options.

        Args:
            interface_callbacks: Validation callbacks to set.
        """
        k.btck_context_options_set_validation_interface(self, interface_callbacks)


class Context(KernelOpaquePtr):
    """The kernel context is used to initialize internal state and hold the chain
    parameters and callbacks for handling error and validation events.
    """

    _create_fn = k.btck_context_create
    _destroy_fn = k.btck_context_destroy

    def __init__(self, options: ContextOptions):
        """Create a kernel context.

        Args:
            options: Context options to use.
        """
        super().__init__(options)

    def interrupt(self) -> int:
        """Interrupt long-running validation functions. Useful for operations like reindexing,
        importing or processing blocks.

        Returns:
            0 if interrupt was successful, non-zero otherwise
        """
        return k.btck_context_interrupt(self)

    def __repr__(self) -> str:
        """Return a string representation of the context."""
        return f"<Context at {hex(id(self))}>"
