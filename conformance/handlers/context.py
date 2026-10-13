from conformance.protocol import Parameters
from conformance.util import parse_enum
import pbk


def btck_context_create(params: Parameters) -> pbk.Context:
    chain_type = parse_enum(params["chain_parameters"]["chain_type"])
    chain_params = pbk.ChainParameters(chain_type)
    opts = pbk.ContextOptions()
    opts.set_chainparams(chain_params)

    return pbk.Context(opts)


def btck_context_destroy(params: Parameters) -> None:
    params["context"].delete()
