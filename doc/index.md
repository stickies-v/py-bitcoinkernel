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
import blocks from disk first:

```py
with open("raw_blocks.txt", "r") as file:
    for line in file.readlines():
        block = pbk.Block(bytes.fromhex(line))
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
