from enum import IntEnum

import pbk.capi.bindings as k
from pbk.capi import KernelOpaquePtr


# TODO: add enum auto-generation or testing to ensure it remains in
# sync with bitcoinkernel.h
class ChainType(IntEnum):
    """Enumeration of supported Bitcoin network types."""

    MAINNET = 0
    """Main Bitcoin network"""

    TESTNET = 1
    """Test Bitcoin network"""

    TESTNET_4 = 2
    """Testnet4 Bitcoin network"""

    SIGNET = 3
    """Signet Bitcoin network"""

    REGTEST = 4
    """Regression test network"""


class ConsensusParams(KernelOpaquePtr):
    """View of the consensus parameters of a chain."""


class ChainParameters(KernelOpaquePtr):
    """Chain parameters describing properties of a Bitcoin network.

    Chain parameters define network-specific constants and rules. These
    are typically passed to [context options][pbk.ContextOptions] when
    creating a kernel context.
    """

    _create_fn = k.btck_chain_parameters_create
    _destroy_fn = k.btck_chain_parameters_destroy
    _copy_fn = k.btck_chain_parameters_copy

    def __init__(self, chain_type: ChainType):
        """Create chain parameters for a specific network type.

        Args:
            chain_type: The Bitcoin network type to configure.

        Raises:
            RuntimeError: If the C constructor fails (propagated from base class).
        """
        super().__init__(chain_type)

    @property
    def consensus_params(self) -> ConsensusParams:
        """The consensus parameters for this chain.

        Returns:
            The consensus parameters. View into these chain parameters.
        """
        return ConsensusParams._from_view(
            k.btck_chain_parameters_get_consensus_params(self), self
        )
