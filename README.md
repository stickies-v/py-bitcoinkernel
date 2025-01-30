# py-bitcoinkernel
[![pypi](https://img.shields.io/pypi/v/py-bitcoinkernel.svg)](https://pypi.python.org/pypi/py-bitcoinkernel)
[![versions](https://img.shields.io/pypi/pyversions/py-bitcoinkernel.svg)](https://github.com/stickies-v/py-bitcoinkernel)
[![license](https://img.shields.io/github/license/stickies-v/py-bitcoinkernel.svg)](https://github.com/stickies-v/py-bitcoinkernel/blob/main/LICENSE)

`py-bitcoinkernel` is a Python wrapper around
[`libbitcoinkernel`](https://github.com/bitcoin/bitcoin/pull/30595)
providing a clean, Pythonic interface while handling the low-level
ctypes bindings and memory management.

In its current alpha state, it is primarily intended as a tool to:
1) help developers experiment with the `libbitcoinkernel` library and to
   help inform its development and interface design.
2) help data scientists access and parse Bitcoin blockchain data for
   research purposes, instead of using alternative interfaces like the
   Bitcoin Core RPC interface or manually parsing block data files.

> [!WARNING]
> `py-bitcoinkernel` is highly experimental software, and should in no
> way be used in software that is consensus-critical, deals with
> (mainnet) coins, or is generally used in any production environment.

## Table of contents

- [Installation](#installation)
- [Usage](#usage)
- [Limitations](#limitations)

## Installation

There are two main ways to install `py-bitcoinkernel`:
1) Installing a pre-compiled wheel from PyPI, if it is available for
   your platform. This is the fastest way to install `py-bitcoinkernel`,
   and does not introduce any further dependencies. This approach
   requires you to trust the wheel build system.
2) Installing from source and letting `pip` compile the dependencies
   locally. This allows you to compile `libbitcoinkernel` from source,
   and is the only way to install `py-bitcoinkernel` on platforms where
   a pre-compiled wheel is not available. It is significantly slower than
   installing a wheel, and requires a number of dependencies to be
   installed.

### Install from wheel

To install a pre-compiled wheel from PyPI, simply run:

```
pip install py-bitcoinkernel
```

### Install from source

You can clone this repository and run:

```
pip install .
```

Alternatively, you can install the source distribution from PyPI:

```
pip install py-bitcoinkernel --no-binary :all:
```

> [!NOTE]
> When installing from source, `pip` will automatically compile
> `libbitcoinkernel` from the bundled source code in `depend/bitcoin/`.
> This process may take a while. To inspect the build progress, add -`v`
> to your `pip` command, e.g.  `pip install . -v`.

### Requirements

This project requires Python 3.10+ and `pip`.

When installing from source, additional requirements apply:
- The minimum system requirements, build requirements and dependencies
  to compile `libbitcoinkernel` from source. See Bitcoin Core's
  documentation
  ([Unix](./depend/bitcoin/doc/build-unix.md),
  [macOS](./depend/bitcoin/doc/build-osx.md),
  [Windows](./depend/bitcoin/doc/build-windows.md))
  for more information.
  - Note: `libevent` is a required dependency for Bitcoin Core, but not
    for `libbitcoinkernel`.

## Usage

> [!WARNING]
> This code is highly experimental and not ready for use in
> production software. The interface is under active development and
> is likely going to change, without concern for backwards compatibility.

All the classes and functions that can be used are exposed in a single
`pbk` package. Lifetimes are managed automatically. The application is
currently not threadsafe.

The entry point for most current `libbitcoinkernel` usage is the
`ChainstateManager`.

### Logging

If you want to enable `libbitcoinkernel` built-in logging, create a
`LoggingConnection()` object and keep it alive for the duration of your
application:

```py
import pbk
log = pbk.LoggingConnection()  # must be kept alive for the duration of the application
```

### Loading a chainstate

First, we'll instantiate a `ChainstateManager` object. If you want
`py-bitcoinkernel` to use an existing `Bitcoin Core` chainstate, copy
the data directory to a new location and point `datadir` at it.

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
        chainman.process_block(block, new_block=True)
```

### Common operations

ChainstateManager exposes a range of functionality to interact with the
chainstate. For example, to print the current block tip:

```py
tip = chainman.get_block_index_from_tip()
print(f"Current block tip: {tip.block_hash.hex} at height {tip.height}")
```

To lazily iterate over the last 10 block indexes, use the
`block_index_generator` function:

```py
from_block = -10  # Negative indexes are relative to the tip
to_block = -1     # -1 is the chain tip
for block_index in pbk.block_index_generator(chainman, from_block, to_block):
    print(f"Block {block_index.height}: {block_index.block_hash.hex}")
```

Block indexes can be used for other operations, like reading blocks from
disk:

```py
block_height = 1
block_index = chainman.get_block_index_from_height(block_height)
block = chainman.read_block_from_disk(block_index)
filename = f"block_{block_height}.bin"
print(f"Writing block {block_height}: {block_index.block_hash.hex} to disk ({filename})...")
with open(filename, "wb") as f:
    f.write(block.data)
```

## Limitations

- `Bitcoin Core` requires exclusive access to its data directory. If you
  want to use `py-bitcoinkernel` with an existing chainstate, you'll
  need to either first shut down `Bitcoin Core`, or clone the `blocks/`
  and `chainstate/` directories to a new location.

## Resources
Some helpful resources for learning about `libbitcoinkernel`:

- The [Bitcoin Core PR](https://github.com/bitcoin/bitcoin/pull/30595)
  that introduces the `libbitcoinkernel` C API.
- The `libbitcoinkernel` project [tracking issue](https://github.com/bitcoin/bitcoin/issues/27587).
- ["The Bitcoin Core Kernel"](https://thecharlatan.ch/Kernel/) blog post by TheCharlatan
- The rust-bitcoinkernel [repository](https://github.com/TheCharlatan/rust-bitcoinkernel/)
