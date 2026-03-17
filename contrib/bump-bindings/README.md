# Updating the Bitcoin Core dependency

The `depend/bitcoin/` directory is a subtree of
[bitcoin/bitcoin](https://github.com/bitcoin/bitcoin). It is the source for building
`bitcoinkernel`, whose C header (`depend/bitcoin/src/kernel/bitcoinkernel.h`) is used to generate
the Python ctypes bindings in `src/pbk/capi/bindings.py`.

## Prerequisites

Install the bindings dependencies:

```bash
pip install -e ".[bindings]"
```

A matching system `libclang` is required. The `clang` Python package version pinned in
`pyproject.toml` must match your installed `libclang`.

## Steps

### 1. Pull the new commit

```bash
git subtree pull --prefix=depend/bitcoin \
  https://github.com/bitcoin/bitcoin <commit-sha> --squash
```

### 2. Regenerate and fix up bindings

```bash
clang2py depend/bitcoin/src/kernel/bitcoinkernel.h -o src/pbk/capi/bindings.py
contrib/bump-bindings/fix-bindings.sh src/pbk/capi/bindings.py
```

To override the clang library path to the correct version, you can set `CLANG_LIBRARY_PATH`:
```bash
CLANG_LIBRARY_PATH=/opt/homebrew/opt/llvm@21/lib clang2py ...
```

`clang2py` generates raw ctypes bindings with a stub library loader. `fix-bindings.sh` replaces the
stub with an import of `BITCOINKERNEL_LIB` from `pbk.capi.library`, which finds the bundled shared
library at runtime.

### 3. Update the Python wrappers

Diff `bitcoinkernel.h` against the previous version to identify added, changed or removed API
functions:

```bash
git diff main -- depend/bitcoin/src/kernel/bitcoinkernel.h
```

For each change, update the corresponding Python wrapper modules in `src/pbk/` (e.g.
`block.py`, `chain.py`, `transaction.py`) and their tests in `test/`.

### 4. Verify

```bash
pip install -e ".[test]"
pytest
```
