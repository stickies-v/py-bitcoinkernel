# Conformance Test Handler

Handler for the [Bitcoin Kernel Binding Conformance
Tests](https://github.com/stringintech/kernel-bindings-tests/), allowing
py-bitcoinkernel to be validated against the reference tests.

## Requirements

`pbk` (py-bitcoinkernel) must be installed before running the handler.

## Usage

The handler can be used directly by providing it with inputs via stdin:

```bash
echo '{"id":"chain#1","method":"btck_context_create","params":{"chain_parameters":{"chain_type":"btck_ChainType_REGTEST"}},"ref":"$context"}
{"id":"chain#2","method":"btck_chainstate_manager_create","params":{"context":{"ref":"$context"}},"ref":"$chainstate_manager"}' | ./conformance/run
```

Or interactively to allow debugging with `pdb`:

```bash
./conformance/run
{"id":"chain#1","method":"btck_context_create","params":{"chain_parameters":{"chain_type":"btck_ChainType_REGTEST"}},"ref":"$context"}
{"id":"chain#2","method":"btck_chainstate_manager_create","params":{"context":{"ref":"$context"}},"ref":"$chainstate_manager"}{"result": {"ref": "$context"}, "error": null}
```

Or with the `kernel-bindings-tests` runner:

```bash
cd kernel-bindings-tests
./build/runner --handler ../py-bitcoinkernel/conformance/run
```
