import copy

from conformance.protocol import Parameters
import pbk


def btck_transaction_create(params: Parameters) -> pbk.Transaction:
    return pbk.Transaction(bytes.fromhex(params["raw_transaction"]))


def btck_transaction_destroy(params: Parameters) -> None:
    params["transaction"].delete()


def btck_transaction_copy(params: Parameters) -> pbk.Transaction:
    return copy.copy(params["transaction"].value)


def btck_transaction_to_bytes(params: Parameters) -> str:
    return bytes(params["transaction"].value).hex()


def btck_transaction_get_txid(params: Parameters) -> pbk.Txid:
    return params["transaction"].value.txid


def btck_transaction_count_inputs(params: Parameters) -> int:
    return len(params["transaction"].value.inputs)


def btck_transaction_count_outputs(params: Parameters) -> int:
    return len(params["transaction"].value.outputs)


def btck_transaction_get_input_at(params: Parameters) -> pbk.TransactionInput:
    return params["transaction"].value.inputs[int(params["input_index"])]


def btck_transaction_get_output_at(params: Parameters) -> pbk.TransactionOutput:
    return params["transaction"].value.outputs[int(params["output_index"])]


def btck_transaction_input_copy(params: Parameters) -> pbk.TransactionInput:
    return copy.copy(params["transaction_input"].value)


def btck_transaction_input_destroy(params: Parameters) -> None:
    params["transaction_input"].delete()


def btck_transaction_input_get_out_point(params: Parameters) -> pbk.TransactionOutPoint:
    return params["transaction_input"].value.out_point


def btck_transaction_out_point_copy(params: Parameters) -> pbk.TransactionOutPoint:
    return copy.copy(params["transaction_out_point"].value)


def btck_transaction_out_point_destroy(params: Parameters) -> None:
    params["transaction_out_point"].delete()


def btck_transaction_out_point_get_index(params: Parameters) -> int:
    return params["transaction_out_point"].value.index


def btck_transaction_out_point_get_txid(params: Parameters) -> pbk.Txid:
    return params["transaction_out_point"].value.txid


def btck_transaction_output_create(params: Parameters) -> pbk.TransactionOutput:
    return pbk.TransactionOutput(params["script_pubkey"].value, params["amount"])


def btck_transaction_output_destroy(params: Parameters) -> None:
    params["transaction_output"].delete()


def btck_transaction_output_copy(params: Parameters) -> pbk.TransactionOutput:
    return copy.copy(params["transaction_output"].value)


def btck_transaction_output_get_amount(params: Parameters) -> int:
    return params["transaction_output"].value.amount


def btck_transaction_output_get_script_pubkey(params: Parameters) -> pbk.ScriptPubkey:
    return params["transaction_output"].value.script_pubkey
