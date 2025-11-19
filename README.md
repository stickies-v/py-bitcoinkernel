# py-bitcoinkernel
[![pypi](https://img.shields.io/pypi/v/py-bitcoinkernel.svg)](https://pypi.python.org/pypi/py-bitcoinkernel)
[![versions](https://img.shields.io/pypi/pyversions/py-bitcoinkernel.svg)](https://github.com/stickies-v/py-bitcoinkernel)
[![license](https://img.shields.io/github/license/stickies-v/py-bitcoinkernel.svg)](https://github.com/stickies-v/py-bitcoinkernel/blob/main/LICENSE)

`py-bitcoinkernel` (or `pbk` in short) is a Python wrapper around
[`libbitcoinkernel`](https://github.com/bitcoin/bitcoin/pull/30595)
providing a clean, Pythonic interface while handling the low-level
ctypes bindings and memory management.


> [!WARNING]
> `py-bitcoinkernel` is highly experimental software, and should in no
> way be used in software that is consensus-critical, deals with
> (mainnet) coins, or is generally used in any production environment.

## Installation

To install a pre-compiled wheel from PyPI, simply run:

```
pip install py-bitcoinkernel
```

See the install section in the
[documentation](https://stickies-v.github.io/py-bitcoinkernel/) for more
information and alternative approaches.

## Help

See the [documentation](https://stickies-v.github.io/py-bitcoinkernel/)
for more information, usage examples, and more. You can serve the
documentation locally. First install the dependencies:

```sh
pip install ".[docs,docs-test]"
```

Then generate and serve the documentation with:

```sh
mkdocs serve
```

Documentation coverage can be generated with `interrogate`, e.g.

```sh
interrogate src -v
```