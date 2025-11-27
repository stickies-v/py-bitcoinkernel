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
    NONE = 0  # btck_ScriptVerificationFlags_NONE
    P2SH = 1 << 0  # btck_ScriptVerificationFlags_P2SH
    DERSIG = 1 << 2  # btck_ScriptVerificationFlags_DERSIG
    NULLDUMMY = 1 << 4  # btck_ScriptVerificationFlags_NULLDUMMY
    CHECKLOCKTIMEVERIFY = 1 << 9  # btck_ScriptVerificationFlags_CHECKLOCKTIMEVERIFY
    CHECKSEQUENCEVERIFY = 1 << 10  # btck_ScriptVerificationFlags_CHECKSEQUENCEVERIFY
    WITNESS = 1 << 11  # btck_ScriptVerificationFlags_WITNESS
    TAPROOT = 1 << 17  # btck_ScriptVerificationFlags_TAPROOT
    ALL = (
        P2SH
        | DERSIG
        | NULLDUMMY
        | CHECKLOCKTIMEVERIFY
        | CHECKSEQUENCEVERIFY
        | WITNESS
        | TAPROOT
    )  # btck_ScriptVerificationFlags_ALL


# TODO: add enum auto-generation or testing to ensure it remains in
# sync with bitcoinkernel.h
class ScriptVerifyStatus(IntEnum):
    OK = 0  # btck_ScriptVerifyStatus_SCRIPT_VERIFY_OK
    ERROR_INVALID_FLAGS_COMBINATION = (
        1  # btck_ScriptVerifyStatus_ERROR_INVALID_FLAGS_COMBINATION
    )
    ERROR_SPENT_OUTPUTS_REQUIRED = (
        2  # btck_ScriptVerifyStatus_ERROR_SPENT_OUTPUTS_REQUIRED
    )
    INVALID = -1


class ScriptVerifyException(KernelException):
    script_verify_status: ScriptVerifyStatus

    def __init__(self, status: ScriptVerifyStatus):
        super().__init__(f"Script verification failed: {status.name}")
        self.script_verify_status = status


class ScriptPubkey(KernelOpaquePtr):
    _create_fn = k.btck_script_pubkey_create
    _destroy_fn = k.btck_script_pubkey_destroy

    def __init__(self, data: bytes):
        super().__init__((ctypes.c_ubyte * len(data))(*data), len(data))

    def __bytes__(self) -> bytes:
        writer = ByteWriter()
        return writer.write(k.btck_script_pubkey_to_bytes, self)

    def __repr__(self) -> str:
        hex_str = str(self)
        preview = hex_str[:32] + "..." if len(hex_str) > 32 else hex_str
        return f"<ScriptPubkey len={len(bytes(self))} hex={preview}>"

    def __str__(self) -> str:
        return bytes(self).hex()


def verify_script(
    script_pubkey: ScriptPubkey,
    amount: int,
    tx_to: "Transaction",
    spent_outputs: list["TransactionOutput"] | None,
    input_index: int,
    flags: int,
) -> bool:
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
