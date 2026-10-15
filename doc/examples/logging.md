# Logging

`pbk` forwards `bitcoinkernel` log entries to Python's `logging` module,
so you configure kernel logs like the logs of any other library. There
is nothing to set up in `pbk` itself.

```py
import logging
import pbk

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [%(name)s] [%(funcName)s] %(message)s",
)
```

## Loggers

Entries go to the logger of their category:

| Logger | Entries |
|---|---|
| `btck` | Entries without a specific category, e.g. most INFO, WARNING and ERROR entries |
| `btck.BENCH` | Benchmarking and performance metrics |
| `btck.BLOCKSTORAGE` | Block storage operations |
| `btck.COINDB` | Coin database operations |
| `btck.KERNEL` | General kernel operations |
| `btck.LEVELDB` | LevelDB database operations |
| `btck.LOCK` | Lock contention |
| `btck.MEMPOOL` | Memory pool (mempool) operations |
| `btck.PRUNE` | Block pruning operations |
| `btck.RAND` | Random number generation |
| `btck.REINDEX` | Blockchain reindexing operations |
| `btck.TXPACKAGES` | Transaction package operations |
| `btck.VALIDATION` | Block and transaction validation |

A level that you set on a category logger overrides the global level.
For example, to also see the DEBUG logs of validation (all DEBUG log
output is noisy):

```py
logging.getLogger("btck.VALIDATION").setLevel(logging.DEBUG)
```

Or, with `dictConfig`:

```py
import logging.config

logging.config.dictConfig(
    {
        "version": 1,
        "handlers": {"console": {"class": "logging.StreamHandler"}},
        "root": {"level": "INFO", "handlers": ["console"]},
        "loggers": {
            "btck": {"level": "WARNING"},  # no kernel INFO logs...
            "btck.VALIDATION": {"level": "DEBUG"},  # ...except for validation
        },
    }
)
```

The kernel levels map to the Python levels, plus TRACE, which has
level 5 (`logging.DEBUG - 5`) and level name `TRACE`.

> [!NOTE]
> The kernel only produces entries at or above one global minimum
> level. `pbk` keeps that level at the lowest level that any `btck`
> logger is enabled for, and updates it each time a logger level
> changes. When no `btck` logger is enabled for DEBUG, DEBUG entries
> are not produced at all. When one is, the kernel produces the DEBUG
> entries of all categories, and Python drops the ones you did not
> enable.

## Log records

The records have the standard attributes. `threadName` is the name of
the kernel thread that logged the entry, or of the Python thread if the
kernel logged it on a Python thread. Control characters and line
breaks in messages are escaped (e.g. `\n`, `\t`, `\x1b`), so each
message is printable and fits on one line.

The records also have these attributes:

| Attribute | Value |
|---|---|
| `btck_category` | Category name, e.g. `"VALIDATION"`, or `"NONE"` |
| `btck_timestamp_ns` | Wall-clock time of the entry, in nanoseconds since the Unix epoch |
| `btck_mocktime_s` | Mock time in effect, in seconds since the Unix epoch, or 0 |

You can use them in format strings. Records of other loggers do not
have them, so give a default to prevent a formatting error (in
`dictConfig`, the `defaults` key needs Python 3.12 or newer):

```py
formatter = logging.Formatter(
    "%(asctime)s [%(btck_category)s] %(message)s",
    defaults={"btck_category": "-"},
)
```

## Slow handlers

The kernel calls the handlers of the `btck` loggers synchronously, from
the kernel thread that logs. While a handler runs, every kernel thread
that logs waits, and validation can slow down. If a handler can be slow
(e.g. a network handler), let a `QueueHandler` take the records, and
handle them in a `QueueListener` thread:

```py
import logging
import logging.handlers
import queue

logging.basicConfig(level=logging.INFO)

log_queue = queue.SimpleQueue()
btck_logger = logging.getLogger("btck")
btck_logger.addHandler(logging.handlers.QueueHandler(log_queue))
btck_logger.propagate = False  # the listener gives the records to the root handlers
listener = logging.handlers.QueueListener(
    log_queue, *logging.getLogger().handlers, respect_handler_level=True
)
listener.start()
# ...
listener.stop()  # handles the remaining records
```

This also makes it safe for a handler to call `pbk` functions, which it
must not do when the kernel calls it directly.
