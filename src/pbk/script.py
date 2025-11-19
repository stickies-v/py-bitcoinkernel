import ctypes
import typing
from enum import IntEnum

import pbk.capi.bindings as k
from pbk.capi import KernelOpaquePtr
from pbk.util.exc import KernelException
from pbk.writer import ByteWriter

if typing.TYPE_CHECKING:
    from pbk.transaction import Transaction, TransactionOutput


# TODO: add enum auto-generation or testing to ensure it remains in
# sync with bitcoinkernel.h
class ScriptVerificationFlags(IntEnum):
    """Script verification flags that may be composed with each other.

    These flags control which validation rules are enforced during script
    verification. Multiple flags can be combined using bitwise OR operations.
    """

    NONE = 0  #: No verification flags
    P2SH = 1 << 0  #: Evaluate P2SH subscripts (BIP16)
    DERSIG = 1 << 2  #: Enforce strict DER signature encoding (BIP66)
    NULLDUMMY = 1 << 4  #: Enforce NULLDUMMY rule (BIP147)
    CHECKLOCKTIMEVERIFY = 1 << 9  #: Enable CHECKLOCKTIMEVERIFY opcode (BIP65)
    CHECKSEQUENCEVERIFY = 1 << 10  #: Enable CHECKSEQUENCEVERIFY opcode (BIP112)
    WITNESS = 1 << 11  #: Enable Segregated Witness (BIP141)
    TAPROOT = 1 << 17  #: Enable Taproot (BIP341 & BIP342)
    ALL = (  #: All verification flags combined
        P2SH
        | DERSIG
        | NULLDUMMY
        | CHECKLOCKTIMEVERIFY
        | CHECKSEQUENCEVERIFY
        | WITNESS
        | TAPROOT
    )


# TODO: add enum auto-generation or testing to ensure it remains in
# sync with bitcoinkernel.h
class ScriptVerifyStatus(IntEnum):
    """Status codes returned by script verification.

    These codes indicate the result of script verification, including
    success, various error conditions, and validation failures.
    """

    OK = 0  #: Verification succeeded
    ERROR_INVALID_FLAGS_COMBINATION = (
        1  #: The verification flags were combined in an invalid way
    )
    ERROR_SPENT_OUTPUTS_REQUIRED = (
        2  #: The taproot flag requires valid spent outputs to be provided
    )


class ScriptVerifyException(KernelException):
    """Exception raised when script verification fails.

    This exception is raised by the [ScriptPubkey.verify][pbk.ScriptPubkey.verify]
    function when a script does not pass validation. The exception includes a
    status code that provides details about why verification failed.

    Attributes:
        status: The status code indicating the failure reason.
    """

    status: ScriptVerifyStatus

    def __init__(self, status: ScriptVerifyStatus):
        """Create a script verification exception.

        Args:
            status: The verification status code indicating the failure reason.
        """
        super().__init__(f"Script verification failed: {status.name}")
        self.status = status


class ScriptPubkey(KernelOpaquePtr):
    """A Bitcoin script defining spending conditions for an output."""

    _create_fn = k.btck_script_pubkey_create
    _destroy_fn = k.btck_script_pubkey_destroy

    def __init__(self, data: bytes):
        """Create a script pubkey from raw script data.

        Args:
            data: The script pubkey data containing opcodes and operands.

        Raises:
            RuntimeError: If the C constructor fails (propagated from base class).
        """
        super().__init__((ctypes.c_ubyte * len(data))(*data), len(data))

    def __bytes__(self) -> bytes:
        """Serialize the script pubkey to bytes.

        Returns:
            The raw script data.
        """
        writer = ByteWriter()
        return writer.write(k.btck_script_pubkey_to_bytes, self)

    def __repr__(self) -> str:
        """Return a string representation of the script pubkey."""
        hex_str = str(self)
        preview = hex_str[:32] + "..." if len(hex_str) > 32 else hex_str
        return f"<ScriptPubkey len={len(bytes(self))} hex={preview}>"

    def __str__(self) -> str:
        """Get the hexadecimal representation of the script.

        Returns:
            The script data as a hex string.
        """
        return bytes(self).hex()

    def verify(
        self,
        amount: int,
        tx_to: "Transaction",
        spent_outputs: list["TransactionOutput"] | None,
        input_index: int,
        flags: int,
    ) -> bool:
        """Verify that a transaction input correctly spends this script pubkey.

        This function validates whether the input at the specified index in the
        spending transaction satisfies the conditions defined by the script pubkey.
        The verification process depends on the flags provided, which control which
        consensus rules are enforced.

        Args:
            amount: The value of the output being spent, in satoshis. Required
                when VERIFY_WITNESS flag is set.
            tx_to: The transaction that is attempting to spend the output.
            spent_outputs: All outputs being spent by the transaction. Required
                when VERIFY_TAPROOT flag is set, otherwise can be None.
            input_index: The zero-based index of the input in `tx_to` that is
                spending the script pubkey.
            flags: Bitfield of ScriptFlags controlling which validation rules to
                enforce. Use ScriptFlags values combined with bitwise OR.

        Returns:
            True if the script verification succeeds.

        Raises:
            ScriptVerifyException: If script verification fails. The exception
                contains a status code indicating the specific failure reason.
        """
        spent_outputs_array = (
            (ctypes.POINTER(k.btck_TransactionOutput) * len(spent_outputs))(
                *[output._as_parameter_ for output in spent_outputs]
            )
            if spent_outputs
            else None
        )
        spent_outputs_len = len(spent_outputs) if spent_outputs else 0
        k_status = k.btck_ScriptVerifyStatus(ScriptVerifyStatus.OK)
        success = k.btck_script_pubkey_verify(
            self,
            amount,
            tx_to,
            spent_outputs_array,
            spent_outputs_len,
            ctypes.c_uint32(input_index),
            ctypes.c_uint32(flags),
            k_status,
        )

        status = ScriptVerifyStatus(k_status.value)
        if not success and status != ScriptVerifyStatus.OK:
            raise ScriptVerifyException(status)

        return success
