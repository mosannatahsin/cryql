"""Measure recovery against the synthetic lab; never writes fabricated results."""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
import threading
import time
from http.server import ThreadingHTTPServer
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from cryql.config import CryQLConfig
from cryql.orchestrator import discover
from cryql.recovery import recover
from lab.server import Handler


def run(port: int = 0) -> dict:
    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    Handler.suggestions = True
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    started = time.perf_counter()
    try:
        url = f"http://127.0.0.1:{server.server_port}/graphql"
        config = CryQLConfig(allow_private=True, rate_limit=0, max_requests=30)
        Handler.introspection = True
        introspected = asyncio.run(discover(url, config))
        Handler.introspection = False
        recovered_result = asyncio.run(recover(url, ["user", "health", "id", "name", "search", "status", "missing"], config))
        recovered = set(recovered_result.graph.types["Query"].fields)
        expected = {"user", "health", "search", "status"}
        true_positive = len(recovered & expected)
        return {
            "runtime_seconds": round(time.perf_counter() - started, 6),
            "cases": {
                "introspection_enabled": {
                    "requests": 1,
                    "fields": sorted(introspected.types.get("Query").fields),
                    "relationships": introspected.relationships,
                },
                "introspection_disabled_recovery": {
                    "requests": recovered_result.requests,
                    "field_precision": true_positive / len(recovered) if recovered else 1.0,
                    "field_recall": true_positive / len(expected),
                    "nested_fields": sorted(recovered_result.graph.types["User"].fields),
                    "enum_values": sorted(recovered_result.graph.types["Status"].enum_values),
                    "input_fields": sorted(recovered_result.graph.types["SearchFilter"].input_fields),
                    "relationships": recovered_result.graph.relationships,
                    "errors": recovered_result.errors,
                },
            },
        }
    finally:
        server.shutdown()
        thread.join(timeout=2)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output")
    args = parser.parse_args()
    report = run()
    text = json.dumps(report, indent=2) + "\n"
    if args.output:
        with open(args.output, "w", encoding="utf-8") as handle:
            handle.write(text)
    else:
        print(text, end="")


if __name__ == "__main__":
    main()
