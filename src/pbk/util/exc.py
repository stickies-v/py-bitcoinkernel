class KernelException(Exception):
    """Base class for errors emitted by this library."""

    pass


class ProcessBlockException(KernelException):
    """Raised when ChainstateManager fails to process a block."""

    def __init__(self, code: int):
        """Create a block processing exception.

        Args:
            code: The error code returned by the C API.
        """
        self.code = code
        super().__init__(f"Block processing failed with error code {code}")
