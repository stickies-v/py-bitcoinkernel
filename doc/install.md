# Installation

There are two main ways to install `py-bitcoinkernel`:

1. Installing a [pre-compiled wheel](#install-from-wheel) from
   [PyPI](https://pypi.org/project/py-bitcoinkernel), if it is available
   for your platform. This is the fastest way to install
   `py-bitcoinkernel`, and does not introduce any further dependencies.
   This approach requires you to trust the wheel build system.
2. Installing [from source](#install-from-source)) and letting `pip`
   compile the dependencies locally. This allows you to compile
   `libbitcoinkernel` from source, and is the only way to install
   `py-bitcoinkernel` on platforms where a pre-compiled wheel is not
   available. It is significantly slower than installing a wheel, and
   requires a number of dependencies to be installed.

## Install from wheel

To install a pre-compiled wheel from PyPI, simply run:

```
pip install py-bitcoinkernel
```

## Install from source

You can clone this repository and run:

```
pip install .
```

Alternatively, you can install the source distribution from PyPI:

```
pip install py-bitcoinkernel --no-binary :all:
```

!!! note
    When installing from source, `pip` will automatically compile
    `libbitcoinkernel` from the bundled source code in `depend/bitcoin/`.
    This process may take a while. To inspect the build progress, add -`v`
    to your `pip` command, e.g.  `pip install . -v`.

## Requirements

This project requires Python 3.10+ and `pip`.

When installing from source, additional requirements apply:
- The minimum system requirements, build requirements and dependencies
  to compile `libbitcoinkernel` from source. See Bitcoin Core's
  documentation
  ([Unix](https://github.com/stickies-v/py-bitcoinkernel/blob/main/depend/bitcoin/doc/build-unix.md),
  [macOS](https://github.com/stickies-v/py-bitcoinkernel/blob/main/depend/bitcoin/doc/build-osx.md),
  [Windows](https://github.com/stickies-v/py-bitcoinkernel/blob/main/depend/bitcoin/doc/build-windows.md))
  for more information.
  - Note: `libevent` is a required dependency for Bitcoin Core, but not
    for `libbitcoinkernel`.
