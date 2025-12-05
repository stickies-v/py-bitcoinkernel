#!/usr/bin/env python3
"""
Simple Python handler for Bitcoin Kernel conformance tests.

This handler conforms to the handler-spec.md protocol:
- Reads JSON requests from stdin (one per line)
- Writes JSON responses to stdout (one per line)
- Processes requests sequentially
- Exits cleanly when stdin closes
"""

from dataclasses import asdict, dataclass
from enum import Enum
from functools import reduce
import json
from operator import or_
import sys
from typing import Any, Dict, Optional

import pbk


def parse_enum(value: str):
    prefix, type_str, member = value.split("_", maxsplit=2)
    assert prefix == "btck"
    return getattr(pbk, type_str)[member]


@dataclass
class Request:
    """Represents an incoming request."""

    id: str
    method: str
    params: Optional[Dict[str, Any]] = None


@dataclass
class Response:
    """Represents an outgoing response."""

    id: str
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


class Handler:
    """Main handler class for processing requests."""

    def handle_request(self, request: Request) -> Response:
        """
        Process a single request and return a response.
        """
        if request.method == "btck_script_pubkey_verify":
            return self.handle_script_verify(request)
        else:
            return Response(id=request.id, error={"code": {"type": "UNKNOWN_METHOD"}})

    def handle_script_verify(self, request: Request) -> Response:
        """
        Handle btck_script_pubkey_verify requests.
        """
        flags = reduce(or_, (parse_enum(f) for f in request.params["flags"]), 0)
        spk = pbk.ScriptPubkey(bytes.fromhex(request.params["script_pubkey"]))
        try:
            is_valid = spk.verify(
                request.params["amount"],
                pbk.Transaction(bytes.fromhex(request.params["tx_to"])),
                [
                    pbk.TransactionOutput(
                        pbk.ScriptPubkey(bytes.fromhex(so["script_pubkey"])),
                        so["amount"],
                    )
                    for so in request.params["spent_outputs"]
                ],
                request.params["input_index"],
                flags,
            )

            return Response(id=request.id, result=bool(is_valid))

        except pbk.ScriptVerifyException as e:
            return Response(
                id=request.id, error={"code": asdict(CodeError.from_enum(e.status))}
            )


def main():
    """Main entry point - read requests from stdin and process them."""
    handler = Handler()
    request_data = {}

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            request_data = json.loads(line)
            request = Request(**request_data)
            response = handler.handle_request(request)
            response.write()
        except Exception as e:
            # Try to send a JSON error back if possible
            if req_id := request_data.get("id"):
                resp = Response(
                    id=req_id,
                    error={
                        "code": {"type": f"HandlerError {(str(e))}", "member": str(e)}
                    },
                )
                resp.write()


if __name__ == "__main__":
    main()
