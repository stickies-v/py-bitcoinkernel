# Python-bitcoinlib Examples

The [`python-bitcoinlib`](https://github.com/petertodd/python-bitcoinlib)
library allows constructing various objects from bytes. We can use this
to more granularly inspect kernel objects that expose their contents as
bytes, such as [`Block`](#inspecting-block-data) (`kernel_Block`) and
[`TransactionOutput`](#inspecting-transactionoutput-data)
(`kernel_TransactionOutput`).

> [!NOTE]
> The `python-bitcoinlib` library is unrelated to this project, and
> information here is provided only on a best-effort basis.

## Setup

First, we'll create a ChainstateManager and load the current chain tip:

```py
import pbk
chainman = pbk.load_chainman("/tmp/bitcoin/signet/", pbk.ChainType.SIGNET)
tip = chainman.get_block_index_from_tip()
```

## Inspecting Block Data

To analyze the block, we can use the `python-bitcoinlib` `CBlock` class:

```py
from bitcoin.core import CBlock

block_bytes = chainman.read_block_from_disk(tip).data
cblock = CBlock.deserialize(block_bytes)

assert tip.block_hash.hex == cblock.GetHash().hex()
print(f"Block {cblock.GetHash().hex()} has {len(cblock.vtx)} transactions and {cblock.GetWeight()} weight")
print(f"The last transaction has witness data: {cblock.vtx[-1].wit.vtxinwit}")
```

## Inspecting TransactionOutput data

```py
from bitcoin.core.script import CScript
from pprint import pprint

undo = chainman.read_block_undo_from_disk(tip)
result = {}
for i, tx in enumerate(undo.iter_transactions()):
    result[i] = [CScript(output.script_pubkey.data) for output in tx.iter_outputs()]
print(f"Block {tip.height} has transactions spending the following previous outputs:")
pprint(result)
```
