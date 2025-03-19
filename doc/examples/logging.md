# Logging

The easiest way to inspect `bitcoinkernel` logs is using a
[`KernelLogViewer`](#kernellogviewer) which integrates with python's
`logging`. Alternatively, [custom logging](#custom-logging) can be
implemented.

## KernelLogViewer

```py
import logging
import pbk

FORMAT = "%(asctime)s [%(levelname)s] [%(name)s] [%(funcName)s] %(message)s"

logging.basicConfig(
    level=logging.INFO,
    format=FORMAT,
    handlers=[
        logging.FileHandler("my-log.log"),
        logging.StreamHandler()
    ]
)

logger = pbk.KernelLogViewer()
```

To inspect DEBUG logs, set the appropriate `logging.DEBUG` level and
initialize `KernelLogViewer` with the categories you want the log output
for (or `pbk.LogCategory.ALL` to view all DEBUG log output, which is noisy).

```py
logging.basicConfig(
    level=logging.DEBUG,
    format=FORMAT,
    handlers=[
        logging.FileHandler("my-log.log"),
        logging.StreamHandler()
    ]
)

logger = pbk.KernelLogViewer(categories=[pbk.LogCategory.VALIDATION])
```

DEBUG categories can also be enabled temporarily with a context manager.
For example, to inspect validation logs during the initialization of
a `ChainstateManager`:

```py
logger = pbk.KernelLogViewer()  # no debug categories are enabled
with logger.temporary_categories(categories=[pbk.LogCategory.LEVELDB]):
    chainman = pbk.load_chainman("/tmp/bitcoin/signet", pbk.ChainType.SIGNET)
```

> [!IMPORTANT]
> `KernelLogViewer` objects MUST be kept alive for the
> duration of the program (or for as long as logging is necessary), the
> logging connection will automatically be destroyed as soon as the
> `KernelLogViewer` object goes out of scope.

## Custom logging

`KernelLogViewer` is a convenience class around the
`kernel_LoggingConnection`, which allows any callback that takes a
single string argument.

For example, to implement your own logging with a simple print
statement:


```py
import pbk

def print_no_newline(msg: str) -> None:
    """`bitcoinkernel` log messages already contain a newline."""
    print(msg, end="")

log_opts = pbk.LoggingOptions(log_timestamps=True)

log = pbk.LoggingConnection(cb=print_no_newline, opts=log_opts)
```

> [!IMPORTANT]
> `LoggingConnection` objects MUST be kept alive for the
> duration of the program (or for as long as logging is necessary), the
> logging connection will automatically be destroyed as soon as the
> `LoggingConnection` object goes out of scope.
