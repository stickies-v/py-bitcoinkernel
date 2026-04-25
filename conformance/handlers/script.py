from functools import reduce
from operator import or_

from conformance.protocol import Parameters
from conformance.util import parse_enum
import pbk


def btck_script_pubkey_create(params: Parameters) -> pbk.ScriptPubkey:
    return pbk.ScriptPubkey(bytes.fromhex(params["script_pubkey"]))


def btck_script_pubkey_destroy(params: Parameters) -> None:
    params["script_pubkey"].delete()


def btck_script_pubkey_verify(params: Parameters) -> bool:
    flags = reduce(or_, (parse_enum(f) for f in params["flags"]), 0)
    spk: pbk.ScriptPubkey = params["script_pubkey"].value
    tx_to: pbk.Transaction = params["tx_to"].value
    precomp_txdata: pbk.PrecomputedTransactionData = params["precomputed_txdata"].value

    return bool(
        spk.verify(
            params["amount"],
            tx_to,
            precomp_txdata,
            params["input_index"],
            flags,
        )
    )


def btck_transaction_create(params: Parameters) -> pbk.Transaction:
    return pbk.Transaction(bytes.fromhex(params["raw_transaction"]))


def btck_transaction_destroy(params: Parameters) -> None:
    params["transaction"].delete()


def btck_transaction_output_create(params: Parameters) -> pbk.TransactionOutput:
    spk: pbk.ScriptPubkey = params["script_pubkey"].value
    return pbk.TransactionOutput(spk, params["amount"])


def btck_transaction_output_destroy(params: Parameters) -> None:
    params["transaction_output"].delete()


def btck_precomputed_transaction_data_create(
    params: Parameters,
) -> pbk.PrecomputedTransactionData:
    tx_to: pbk.Transaction = params["tx_to"].value
    spent_outputs = [ref.value for ref in params.get("spent_outputs", [])]
    return pbk.PrecomputedTransactionData(tx_to, spent_outputs)


def btck_precomputed_transaction_data_destroy(params: Parameters) -> None:
    params["precomputed_txdata"].delete()
