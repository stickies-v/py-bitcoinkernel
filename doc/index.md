# py-bitcoinkernel

`py-bitcoinkernel` (or `pbk` in short) is a Python wrapper around
[`libbitcoinkernel`](https://github.com/bitcoin/bitcoin/pull/30595)
providing a clean, Pythonic interface while handling the low-level
ctypes bindings and memory management.

In its current alpha state, it is primarily intended as a tool to:

1. help developers experiment with the `libbitcoinkernel` library and to
   help inform its development and interface design.
2. help data scientists access and parse Bitcoin blockchain data for
   research purposes, instead of using alternative interfaces like the
   Bitcoin Core RPC interface or manually parsing block data files.

!!! warning
    `py-bitcoinkernel` is highly experimental software, and should in no
    way be used in software that is consensus-critical, deals with
    (mainnet) coins, or is generally used in any production environment.

## Usage

!!! warning
    This code is highly experimental and not ready for use in
    production software. The interface is under active development and
    is likely going to change, without concern for backwards compatibility.

All the classes and functions that can be used are exposed in a single
`pbk` package. Lifetimes are managed automatically. The library is
[thread-safe](#concurrency).

The entry point for most current `libbitcoinkernel` usage is the
[`ChainstateManager`][pbk.ChainstateManager].

### Logging

If you want to enable `libbitcoinkernel` built-in logging, configure
python's `logging` module and then create a [`KernelLogViewer`]
[pbk.KernelLogViewer].

```py
import logging
import pbk

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s")
log = pbk.KernelLogViewer()  # must be kept alive for the duration of the application
```

See the [Logging API reference](api/logging.md) for more examples
on different ways to configure logging.

### Loading a chainstate

First, we'll instantiate a [`ChainstateManager`][pbk.ChainstateManager]
object. If you want `py-bitcoinkernel` to use an existing `Bitcoin Core`
chainstate, copy the data directory to a new location and point
`datadir` at it.

**IMPORTANT**: `py-bitcoinkernel` requires exclusive access to the data
directory. Sharing a data directory with Bitcoin Core will ONLY work
when only one of both programs is running at a time.

```py
from pathlib import Path
import pbk

datadir = Path("/tmp/bitcoin/signet")
chainman = pbk.load_chainman(datadir, pbk.ChainType.SIGNET)
```

If you're starting from an empty data directory, you'll likely want to
import some blocks first. As an example, we import the first 2 signet
blocks (after the genesis block):

```py
blocks = [
'00000020f61eee3b63a380a477a063af32b2bbc97c9ff9f01f2c4225e973988108000000f575c83235984e7dc4afc1f30944c170462e84437ab6f2d52e16878a79e4678bd1914d5fae77031eccf4070001010000000001010000000000000000000000000000000000000000000000000000000000000000ffffffff025151feffffff0200f2052a010000001600149243f727dd5343293eb83174324019ec16c2630f0000000000000000776a24aa21a9ede2f61c3f71d1defd3fa999dfa36953755c690689799962b48bebd836974e8cf94c4fecc7daa2490047304402205e423a8754336ca99dbe16509b877ef1bf98d008836c725005b3c787c41ebe46022047246e4467ad7cc7f1ad98662afcaf14c115e0095a227c7b05c5182591c23e7e01000120000000000000000000000000000000000000000000000000000000000000000000000000',
'00000020533b53ded9bff4adc94101d32400a144c54edc5ed492a3b26c63b2d686000000b38fef50592017cfafbcab88eb3d9cf50b2c801711cad8299495d26df5e54812e7914d5fae77031ecfdd0b0001010000000001010000000000000000000000000000000000000000000000000000000000000000ffffffff025251feffffff0200f2052a01000000160014fd09839740f0e0b4fc6d5e2527e4022aa9b89dfa0000000000000000776a24aa21a9ede2f61c3f71d1defd3fa999dfa36953755c690689799962b48bebd836974e8cf94c4fecc7daa24900473044022031d64a1692cdad1fc0ced69838169fe19ae01be524d831b95fcf5ea4e6541c3c02204f9dea0801df8b4d0cd0857c62ab35c6c25cc47c930630dc7fe723531daa3e9b01000120000000000000000000000000000000000000000000000000000000000000000000000000',
]
for serialized in blocks:
    block = pbk.Block(bytes.fromhex(serialized))
    chainman.process_block(block)
```

### Common operations

!!! info
    See the [Examples](examples/index.md) section for more common usage examples of `pbk`

`ChainstateManager` exposes a range of functionality to interact with the
chainstate. For example, to print the current block tip:

```py
chain = chainman.get_active_chain()
tip = chain.block_tree_entries[-1]
print(f"Current block tip: {tip.block_hash} at height {tip.height}")
```

To lazily iterate over the last 10 block tree entries:

```py
start = -10  # Negative indexes are relative to the tip
end = 0      # -1 is the chain tip, but slices are upper-bound exclusive
for entry in chain.block_tree_entries[start:end]:
    print(f"Block {entry.height}: {entry.block_hash}")
```

[Block tree entries][pbk.BlockTreeEntry] can be used for other
operations, like [reading][pbk.ChainstateManager.blocks]
[blocks][pbk.Block] from disk:

```py
block_height = 1
entry = chainman.get_active_chain().block_tree_entries[block_height]
block = chainman.blocks[entry]
filename = f"block_{block_height}.bin"
print(f"Writing block {block_height}: {entry.block_hash} to disk ({filename})...")
with open(filename, "wb") as f:
    f.write(bytes(block))
```

### Concurrency

`py-bitcoinkernel` is thread-safe, but should not be used with
`multiprocessing`. See [concurrency documentation](https://github.com/stickies-v/py-bitcoinkernel/blob/main/doc/concurrency.md) for
more information.

## Testing

See the [Developer Notes](https://github.com/stickies-v/py-bitcoinkernel/blob/main/doc/developer-notes.md#testing) for more
information on running the test suite.

## Limitations

- `Bitcoin Core` requires exclusive access to its data directory. If you
  want to use `py-bitcoinkernel` with an existing chainstate, you'll
  need to either first shut down `Bitcoin Core`, or clone the `blocks/`
  and `chainstate/` directories to a new location.
- The `bitcoinkernel` API currently does not offer granular inspection
  of most kernel objects. See the [API Reference](api/block.md) for examples
  on using third-party (de)serialization libraries to convert kernel
  objects to/from bytes.

## Resources
Some helpful resources for learning about `libbitcoinkernel`:

- The [Bitcoin Core PR](https://github.com/bitcoin/bitcoin/pull/30595)
  that introduces the `libbitcoinkernel` C API.
- The `libbitcoinkernel` project [tracking issue](https://github.com/bitcoin/bitcoin/issues/27587).
- ["The Bitcoin Core Kernel"](https://thecharlatan.ch/Kernel/) blog post by TheCharlatan
- The rust-bitcoinkernel [repository](https://github.com/TheCharlatan/rust-bitcoinkernel/)
