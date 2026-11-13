"""Synthetic, dependency-light GraphQL lab server for local testing."""

from __future__ import annotations

import argparse
import json
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


SCHEMA = {
    "Query": {"user": "User", "health": "String", "search": "String", "status": "String"},
    "User": {"id": "ID", "name": "String"},
}


class Handler(BaseHTTPRequestHandler):
    introspection = True
    suggestions = True
    delay = 0.0
    rate_limit = 0
    requests = 0

    def do_POST(self) -> None:
        Handler.requests += 1
        if Handler.rate_limit and Handler.requests > Handler.rate_limit:
            self.send_response(429)
            self.end_headers()
            return
        if Handler.delay:
            time.sleep(Handler.delay)
        length = int(self.headers.get("Content-Length", "0"))
        body = json.loads(self.rfile.read(length) or b"{}")
        query = body.get("query", "")
        if "__schema" in query and not Handler.introspection:
            self._write({"errors": [{"message": "Introspection is disabled"}]})
            return
        if "__schema" in query:
            self._write({"data": {"__schema": {
                "queryType": {"name": "Query"}, "mutationType": None, "subscriptionType": None,
                "types": [
                    {"name": "Query", "kind": "OBJECT", "fields": [
                        {"name": "user", "args": [{"name": "id", "type": {"kind": "NON_NULL", "name": None, "ofType": {"kind": "SCALAR", "name": "ID", "ofType": None}}, "defaultValue": None}], "type": {"kind": "OBJECT", "name": "User", "ofType": None}},
                        {"name": "health", "args": [], "type": {"kind": "SCALAR", "name": "String", "ofType": None}},
                    ], "inputFields": None, "enumValues": None, "possibleTypes": None},
                    {"name": "User", "kind": "OBJECT", "fields": [
                        {"name": "id", "args": [], "type": {"kind": "SCALAR", "name": "ID", "ofType": None}},
                        {"name": "name", "args": [], "type": {"kind": "SCALAR", "name": "String", "ofType": None}},
                    ], "inputFields": None, "enumValues": None, "possibleTypes": None},
                ],
            }}})
            return
        field = query.split("{", 1)[-1].split("}", 1)[0].strip().split("(", 1)[0]
        if field in SCHEMA["Query"]:
            typ = SCHEMA["Query"][field]
            if field == "user" and "user(" not in query:
                self._write({"errors": [{"message": 'Field "user" argument "id" of type "ID!" is required, but it was not provided.'}]})
                return
            if field == "search" and "search(" not in query:
                self._write({"errors": [{"message": 'Field "search" argument "filter" of type "SearchFilter!" is required, but it was not provided.'}]})
                return
            if field == "status" and "status(" not in query:
                self._write({"errors": [{"message": 'Field "status" argument "value" of type "Status!" is required, but it was not provided.'}]})
                return
            if field == "status" and "status(" in query and "UNKNOWN" not in query:
                self._write({"errors": [{"message": 'Enum "Status" cannot represent non-enum value: "UNKNOWN". Did you mean "ACTIVE" or "INACTIVE"?'}]})
                return
            if field == "search" and "search(" in query and "{}" in query:
                self._write({"errors": [{"message": 'Field "term" of required type "String!" was not provided.'}]})
                return
            if typ in ("String", "ID"):
                self._write({"data": {field: "ok"}})
            elif "{" not in query.split("user", 1)[-1]:
                self._write({"errors": [{"message": f'Field "{field}" of type "{typ}" must have a selection of subfields.'}]})
            else:
                nested = query.split("user", 1)[-1].split("{", 1)[1].split("}", 1)[0].strip()
                if nested in SCHEMA["User"]:
                    self._write({"data": {"user": {nested: "ok"}}})
                else:
                    self._write({"errors": [{"message": f'Cannot query field "{nested}" on type "User". Did you mean "id" or "name"?'}]})
            return
        message = f'Cannot query field "{field}" on type "Query".'
        if Handler.suggestions:
            message += ' Did you mean "user" or "health"?'
        self._write({"errors": [{"message": message}]})

    def _write(self, payload: dict) -> None:
        data = json.dumps(payload).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, *_: object) -> None:
        return


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--no-introspection", action="store_true")
    parser.add_argument("--no-suggestions", action="store_true")
    parser.add_argument("--delay", type=float, default=0.0)
    parser.add_argument("--rate-limit", type=int, default=0)
    args = parser.parse_args()
    Handler.introspection = not args.no_introspection
    Handler.suggestions = not args.no_suggestions
    Handler.delay = args.delay
    Handler.rate_limit = args.rate_limit
    ThreadingHTTPServer((args.host, args.port), Handler).serve_forever()


if __name__ == "__main__":
    main()
