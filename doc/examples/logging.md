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
        logging.StreamHandler(),
    ],
)

logger = pbk.KernelLogViewer()
```

Each [category][pbk.LogCategory] is forwarded to its own child logger,
e.g. `bitcoinkernel.VALIDATION`. To inspect DEBUG logs, initialize
`KernelLogViewer` with a lower [level][pbk.LogLevel], and use the
python logger levels to select the categories you want the DEBUG log
output for (all DEBUG log output is noisy).

```py
logging.basicConfig(
    level=logging.INFO,
    format=FORMAT,
    handlers=[
        logging.FileHandler("my-log.log"),
        logging.StreamHandler(),
    ],
)

logger = pbk.KernelLogViewer(level=pbk.LogLevel.DEBUG)
logger.getLogger(pbk.LogCategory.VALIDATION).setLevel(logging.DEBUG)
```

> [!NOTE]
> The kernel's minimum log level is a global setting. Lower levels
> make the kernel pass more log entries to python, which has a
> performance cost even if python then discards them.

> [!IMPORTANT]
> `KernelLogViewer` objects MUST be kept alive for the
> duration of the program (or for as long as logging is necessary), the
> logging connection will automatically be destroyed as soon as the
> `KernelLogViewer` object goes out of scope.

## Custom logging

`KernelLogViewer` is a convenience class around the
[`LoggingConnection`][pbk.LoggingConnection], which allows any callback
that takes a single [`LogEntry`][pbk.LogEntry] argument.

For example, to implement your own logging with a simple print
statement:


```py
import pbk


def print_entry(entry: pbk.LogEntry) -> None:
    print(f"[{entry.category.name}:{entry.level.name}] {entry.message}")


pbk.logging_set_min_level(pbk.LogLevel.INFO)
log = pbk.LoggingConnection(cb=print_entry)
```

> [!IMPORTANT]
> `LoggingConnection` objects MUST be kept alive for the
> duration of the program (or for as long as logging is necessary), the
> logging connection will automatically be destroyed as soon as the
> `LoggingConnection` object goes out of scope.
