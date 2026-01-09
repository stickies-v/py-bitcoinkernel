"""
Simple Python handler for Bitcoin Kernel conformance tests.

This handler conforms to the handler-spec.md protocol:
- Reads JSON requests from stdin (one per line)
- Writes JSON responses to stdout (one per line)
- Processes requests sequentially
- Exits cleanly when stdin closes
"""

from dataclasses import asdict
import json
import sys

from conformance import handlers
from conformance.protocol import CodeError, Reference, Request, Response
import pbk


class Handler:
    """Main handler class for processing requests."""

    def handle_request(self, request: Request) -> Response:
        """
        Process a single request and return a response.
        """
        try:
            res = self.get_handler(request.method)(request.params)
            if request.ref:
                return Reference(request.ref, res).make_response()
            else:
                return Response(result=res)
        except Exception as exc:
            return self.handle_exception(exc)

    @staticmethod
    def get_handler(method: str):
        return getattr(handlers, method)

    @staticmethod
    def handle_exception(exc: Exception) -> Response:
        if isinstance(exc, pbk.ScriptVerifyException):
            return Response(error={"code": asdict(CodeError.from_enum(exc.status))})

        elif isinstance(exc, RuntimeError):
            return Response(error={})

        raise exc


def main():
    """Main entry point - read requests from stdin and process them."""
    handler = Handler()

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue

        request_data = json.loads(line)
        request = Request(**request_data)
        response = handler.handle_request(request)
        response.write()


if __name__ == "__main__":
    main()
