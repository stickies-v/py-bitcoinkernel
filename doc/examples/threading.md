# Threading

> [!NOTE]
> See also [doc/concurrency.md](../concurrency.md) for more information
> on multithreading.

You can use a ThreadPoolExecutor to speed up slow, I/O-heavy operations
such as reading a block from disk.

```py
import logging
from concurrent.futures import ThreadPoolExecutor

import pbk

logging.basicConfig(level=logging.INFO)
log = pbk.KernelLogViewer()

MAX_WORKERS = 1
READ_N_LAST_BLOCKS = 1000

def process_block(chainman: pbk.ChainstateManager, index: pbk.BlockIndex):
    block_data = chainman.read_block_from_disk(index)
    # implement block processing logic
    # ...
    print(f"Successfully processed block {index.height}")

chainman = pbk.load_chainman("/tmp/bitcoin/signet", pbk.ChainType.SIGNET)
with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
    for idx in pbk.block_index_generator(chainman, start=-READ_N_LAST_BLOCKS):
        pool.submit(process_block, chainman, idx)
```
