import ctypes
import typing
from enum import IntEnum

import pbk.capi.bindings as k
import pbk.util
from pbk.capi import KernelOpaquePtr
from pbk.util.exc import KernelException

if typing.TYPE_CHECKING:
    from pbk.transaction import Transaction, TransactionOutput


class ScriptFlags(IntEnum):
    VERIFY_NONE = k.kernel_SCRIPT_FLAGS_VERIFY_NONE
    VERIFY_P2SH = k.kernel_SCRIPT_FLAGS_VERIFY_P2SH
    VERIFY_DERSIG = k.kernel_SCRIPT_FLAGS_VERIFY_DERSIG
    VERIFY_NULLDUMMY = k.kernel_SCRIPT_FLAGS_VERIFY_NULLDUMMY
    VERIFY_CHECKLOCKTIMEVERIFY = k.kernel_SCRIPT_FLAGS_VERIFY_CHECKLOCKTIMEVERIFY
    VERIFY_CHECKSEQUENCEVERIFY = k.kernel_SCRIPT_FLAGS_VERIFY_CHECKSEQUENCEVERIFY
    VERIFY_WITNESS = k.kernel_SCRIPT_FLAGS_VERIFY_WITNESS
    VERIFY_TAPROOT = k.kernel_SCRIPT_FLAGS_VERIFY_TAPROOT
    VERIFY_ALL = k.kernel_SCRIPT_FLAGS_VERIFY_ALL


class ScriptVerifyStatus(IntEnum):
    OK = k.kernel_SCRIPT_VERIFY_OK
    ERROR_TX_INPUT_INDEX = k.kernel_SCRIPT_VERIFY_ERROR_TX_INPUT_INDEX
    ERROR_INVALID_FLAGS = k.kernel_SCRIPT_VERIFY_ERROR_INVALID_FLAGS
    ERROR_INVALID_FLAGS_COMBINATION = (
        k.kernel_SCRIPT_VERIFY_ERROR_INVALID_FLAGS_COMBINATION
    )
    ERROR_SPENT_OUTPUTS_REQUIRED = k.kernel_SCRIPT_VERIFY_ERROR_SPENT_OUTPUTS_REQUIRED
    ERROR_SPENT_OUTPUTS_MISMATCH = k.kernel_SCRIPT_VERIFY_ERROR_SPENT_OUTPUTS_MISMATCH
    INVALID = -1


class ScriptVerifyException(KernelException):
    script_verify_status: ScriptVerifyStatus

    def __init__(self, status: ScriptVerifyStatus):
        super().__init__(f"Script verification failed: {status.name}")
        self.script_verify_status = status


class ScriptPubkey(KernelOpaquePtr):
    def __init__(self, data: bytes):
        super().__init__((ctypes.c_ubyte * len(data))(*data), len(data))

    @property
    def data(self) -> bytes:
        bytearray = pbk.util.ByteArray._from_ptr(k.kernel_copy_script_pubkey_data(self))
        return bytearray.data


def verify_script(
    script_pubkey: ScriptPubkey,
    amount: int,
    tx_to: "Transaction",
    spent_outputs: list["TransactionOutput"] | None,
    input_index: int,
    flags: int,
) -> bool:
    spent_outputs_array = (
        (ctypes.POINTER(k.kernel_TransactionOutput) * len(spent_outputs))(
            *[output._as_parameter_ for output in spent_outputs]
        )
        if spent_outputs
        else None
    )
    spent_outputs_len = len(spent_outputs) if spent_outputs else 0
    k_status = k.kernel_ScriptVerifyStatus(k.kernel_SCRIPT_VERIFY_OK)
    success = k.kernel_verify_script(
        script_pubkey,
        amount,
        tx_to,
        spent_outputs_array,
        spent_outputs_len,
        ctypes.c_uint32(input_index),
        ctypes.c_uint32(flags),
        k_status,
    )

    status = ScriptVerifyStatus(k_status.value)
    if not success:
        if status == ScriptVerifyStatus.OK:  # TODO: remove once INVALID is added
            status = ScriptVerifyStatus.INVALID
        raise ScriptVerifyException(status)

    return True
