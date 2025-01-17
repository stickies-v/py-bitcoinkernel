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
automatically installs dependencies, including `libbitcoinkernel`.
```
pip install .
```

If `libbitcoinkernel` is already available in your system path, the
installer will automatically use that installation if the version matches
the expected version in `BitcoinkernelVersion.txt`. In case of a mismatch,
the installer will automatically build `libbitcoinkernel` from source in
`depend/bitcoin/`. You can also set the `BITCOINKERNEL_LIB` environment
variable to point to an existing installation of `libbitcoinkernel`:

```
export BITCOINKERNEL_LIB=/path/to/libbitcoinkernel
pip install .
```

In this case, you must ensure that the version of `libbitcoinkernel`
matches the expected version in `BitcoinkernelVersion.txt`.


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
