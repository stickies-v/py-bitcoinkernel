# Python Bitcoin Kernel (pbk)

A Python wrapper around
[libbitcoinkernel](https://github.com/bitcoin/bitcoin/issues/27587)
providing a clean, Pythonic interface while handling the low-level
ctypes bindings and memory management.

## Features

- Clean Python interface that hides ctypes implementation details
- Automatic memory management of kernel resources
- Support for core Bitcoin functionality:
  - Block validation and processing
  - Chain state management
  - Block index traversal

## Installation

### `libbitcoinkernel` shared library

It is recommended to install `py-bitcoinkernel` in a virtual
environment:
```
python -m venv .venv
source .venv/bin/activate
```

The recommended way to install `py-bitcoinkernel` is with `pip`, which
automatically installs dependencies too.
```
pip install . -v
```

`py-bitcoinkernel` is a wrapper around the `libbitcoinkernel` C shared
library, which needs to be installed. The `py-bitcoinkernel` will
automatically try to detect an installation of `libbitcoinkernel`, and
otherwise automatically compile the bundled version in
`depend/bitcoin/`.

If that fails, you can compile it manually with the following commands:

```
NUM_CORES=4
cd depend/bitcoin/
cmake -B cmake -B build -DBUILD_KERNEL_LIB=ON -DBUILD_UTIL_CHAINSTATE=ON
cmake --build build -j $(NUM_CORES)
cmake --install build
```


> [!WARNING] While `libbitcoinkernel` and `py-bitcoinkernel` are in very
> early and experimental phases of development, no version management is
> done, and you **must** install the `libbitcoinkernel` version that is
> shipped with this library in `depend/bitcoin/`.


## Usage

> [!WARNING] This code is highly experimental and not ready for use in
> production software yet.

All the classes and functions that can be used are exposed in a single
`pbk` package. Lifetimes are managed automatically. The application is
currently not threadsafe.

The entry point for most current `libbitcoinkernel` usage is the
`ChainstateManager`. To create it, we'll first need to create a
`Context` object.

### Context

```py
def make_context(chain_type: pbk.ChainType):
    chain_params = pbk.ChainParameters(chain_type)
    opts = pbk.ContextOptions()
    opts.set_chainparams(chain_params)
    return pbk.Context(opts)

context = make_context(pbk.ChainType.SIGNET)
```

### 

If you want to enable `libbitcoinkernel` built-in logging, create a
`LoggingConnection()` object and keep it alive for the duration of your
application:

```py
...
if __name__ == '__main__':
    log = pbk.LoggingConnection()  # must be kept alive for the duration of the application
    <use py-bitcoinkernel>
```
