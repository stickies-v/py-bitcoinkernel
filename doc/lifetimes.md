# Object Lifetimes

`py-bitcoinkernel` exposes two kinds of objects: **owned handles** and
**views**.

## Owned handles

An *owned handle* owns a piece of memory in the underlying kernel
library and is responsible for freeing it when the Python object is
garbage-collected. Owned handles arise in several ways:

- Direct construction:
  ```py
  block = pbk.Block(serialized_block)
  chainman = pbk.load_chainman(datadir)
  ```
- Some accessors and lookups that return a fresh handle, e.g.
  `chainman.blocks[entry]` or `block.block_hash`.
- Explicit promotion of a view via `detach()` or `copy.copy()`
  (see below).

## Views

A *view* is an object obtained from accessing another object. It does
not own its C memory; it borrows it from a *parent*:

```py
tx = block.transactions[0]   # view of `block`
txid = tx.txid               # view of `tx`
output = tx.outputs[0]       # view of `tx`
```

To keep these views safe to use, each one holds a reference back to
its parent. The parent then cannot be garbage-collected until every
view derived from it has been dropped.

### The retention problem

Because views keep their parents alive, holding on to a small derived
object can silently retain a much larger one in memory:

```py
def get_txid(serialized_block: bytes) -> pbk.Txid:
    block = pbk.Block(serialized_block)
    return block.transactions[0].txid
    # The returned Txid is 32 bytes of data, but it keeps the entire
    # `block` (and the transaction view) alive for as long as the
    # caller holds it.
```

## Breaking the link with `detach()`

`detach()` promotes a view to an owned handle by allocating its own
copy of the underlying C data. After detaching, the object no longer
depends on its parent, and the parent can be freed independently:

```py
def get_txid(serialized_block: bytes) -> pbk.Txid:
    block = pbk.Block(serialized_block)
    return block.transactions[0].txid.detach()
    # The detached Txid owns its own C memory; `block` is freed as
    # soon as this function returns.
```

## `copy.copy` and `copy.deepcopy`

Python's standard [`copy`](https://docs.python.org/3/library/copy.html)
module is also supported:

```py
import copy

txid = copy.copy(block.transactions[0].txid)
# Equivalent to `block.transactions[0].txid.detach()`, except
# `copy.copy` returns a *new* object and leaves the original
# view untouched.
```

The difference: `detach()` mutates the receiver in place (and returns
`self`); `copy.copy(obj)` always returns a fresh instance. Both
allocate the same underlying C copy.

For kernel objects, `copy.deepcopy` behaves identically to `copy.copy`
— there is no observable mutable state reachable through these
wrappers, so a "deep" copy is the same as a shallow one.

Types that cannot be detached also cannot be copied; `copy.copy` on
them raises `TypeError`.
