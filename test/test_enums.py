import pbk
import pbk.capi.bindings as k


def test_enums_match():
    to_test = [
        (pbk.ChainType, k.kernel_ChainType__enumvalues),
        (pbk.LogCategory, k.kernel_LogCategory__enumvalues),
        # (pbk.ScriptVerifyStatus, k.kernel_ScriptVerifyStatus__enumvalues),  # TODO: suppressed until INVALID is added
    ]

    for native, autogen in to_test:
        assert len(native) == len(autogen)
