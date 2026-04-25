from dataclasses import asdict, dataclass
from enum import Enum
import json
from typing import Any, Dict, Optional


class Parameters(dict):
    """Dict subclass that resolves ``{"ref": "$name"}`` values to Reference objects on access."""

    def _resolve(self, value):
        """Recursively resolve ref dicts in value, including inside lists."""
        if isinstance(value, dict) and len(value) == 1 and "ref" in value:
            return Reference.get(value["ref"])
        if isinstance(value, list):
            return [self._resolve(item) for item in value]
        return value

    def __getitem__(self, key):
        return self._resolve(super().__getitem__(key))

    def get(self, key, default=None):
        """Like dict.get, but resolves References."""
        try:
            return self[key]
        except KeyError:
            return default


@dataclass
class Request:
    """Represents an incoming request."""

    id: str
    method: str
    params: Optional[Parameters] = None
    ref: Optional[str] = None

    def __post_init__(self):
        self.params = Parameters(self.params)


@dataclass
class Response:
    """Represents an outgoing response."""

    result: Optional[Any] = None
    error: Optional[Dict[str, str]] = None

    def write(self) -> None:
        """Write a response to stdout as JSON."""
        print(json.dumps(asdict(self)), flush=True)


@dataclass
class CodeError:
    type: str
    member: str

    @classmethod
    def from_enum(cls, enum_value: Enum) -> "CodeError":
        """Create a CodeError from an enum value."""
        return cls(type=f"btck_{type(enum_value).__name__}", member=enum_value.name)


class Reference:
    """A reference to a stored resource that can be looked up by name."""

    _all_refs: dict[str, "Reference"] = {}

    def __init__(self, name: str, value: Any):
        self.name = name
        self.value = value
        if name in self._all_refs:
            raise RuntimeError(f"Reference {name} already exists")
        self._all_refs[name] = self

    def delete(self) -> None:
        """Remove this reference from the registry."""
        self._all_refs.pop(self.name, None)

    def make_response(self) -> Response:
        """Create a response that references this object by name."""
        return Response(result={"ref": self.name})

    @classmethod
    def get(cls, name: str) -> "Reference":
        """Look up a reference by name."""
        return cls._all_refs[name]
