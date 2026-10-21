from typing import Any

import pbk


def parse_enum(value: str) -> Any:
    prefix, type_str, member = value.split("_", maxsplit=2)
    assert prefix == "btck"
    return getattr(pbk, type_str)[member]
