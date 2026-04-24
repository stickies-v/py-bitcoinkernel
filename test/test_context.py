import pbk


def test_chain_types() -> None:
    options = pbk.ContextOptions()
    for chain_type in pbk.ChainType:
        options.set_chainparams(pbk.ChainParameters(chain_type))
        context = pbk.Context(options)
        assert context is not None
