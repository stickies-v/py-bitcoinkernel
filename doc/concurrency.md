# Concurrency

`py-bitcoinkernel` is thread-safe, but should not be used with
`multiprocessing`.

## Multithreading

Python generally is not well suited for multithreading, because of the
Global Interpreter Lock (GIL). However, because the `bitcoinkernel`
shared library does not contain any Python bytecode, we can safely
bypass a lot of those limitations.

For that reason, it is recommended to use multiple threads for expensive
operations such as reading blocks from disk. See
[examples/threading.md](./examples/threading.md) for an example
implementation.

### Thread-safety

`py-bitcoinkernel` is safe to use from multiple threads. However,
synchronization (using e.g. `threading.Lock()`) is still required in
some circumstances, including:
- changes to the chainstate (such as advancing the tip, or rolling back)
  may invalidate earlier obtained objects. For example, the result from
  `ChainstateManager.get_block_index_from_tip()` is not guaranteed to
  remain the tip if another thread can advance the chainstate.
- using generators such as `block_index_generator()`, as is commonly
  the case with using generators in multithreaded contexts in Python.

## Parallelism / multiprocessing

`py-bitcoinkernel` currently does **not** support `multiprocessing`,
because most `bitcoinkernel` functionality can currently only be used
from a single process, due to its dependency on and usage of `LevelDB`.
