from __future__ import annotations

import argparse
import asyncio
import logging
from pathlib import Path
from typing import List, Optional

from .artifacts import parse_artifact
from .config import CryQLConfig
from .export import write
from .orchestrator import discover
from .recovery import recover
from .schema import SchemaGraph


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="cryql", description="Evidence-driven GraphQL schema intelligence")
    parser.add_argument("-d", "--domain", required=True, help="GraphQL endpoint URL")
    parser.add_argument("-o", "--output", default="cryql-schema.json")
    parser.add_argument("--threads", "--concurrency", type=int, default=10)
    parser.add_argument("--rate-limit", type=float, default=5.0)
    parser.add_argument("--timeout", type=float, default=10.0)
    parser.add_argument("--retries", type=int, default=2)
    parser.add_argument("--max-requests", type=int, default=100)
    parser.add_argument("--max-duration", type=float, default=120.0)
    parser.add_argument("--proxy")
    parser.add_argument("-H", "--header", action="append", default=[])
    parser.add_argument("--cookie", action="append", default=[])
    parser.add_argument("--artifacts", action="append", default=[])
    parser.add_argument("--recovery", action="store_true", help="use bounded validation-based recovery when introspection is unavailable")
    parser.add_argument("--wordlist", type=argparse.FileType("r"), help="candidate GraphQL names for --recovery")
    parser.add_argument("--format", choices=("json", "sdl", "evidence"), default="json")
    parser.add_argument("--allow-private", action="store_true")
    parser.add_argument("--no-color", action="store_true")
    parser.add_argument("-v", "--verbose", action="store_true")
    parser.add_argument("--debug", action="store_true")
    parser.add_argument("--version", action="version", version="CryQL 1.0.0")
    return parser


def _pairs(values: List[str], label: str) -> dict[str, str]:
    result = {}
    for value in values:
        if ":" not in value:
            raise ValueError(f"{label} must use NAME:VALUE")
        key, val = value.split(":", 1)
        result[key.strip()] = val.strip()
    return result


async def run(args: argparse.Namespace) -> None:
    config = CryQLConfig(timeout=args.timeout, retries=args.retries, concurrency=args.threads, rate_limit=args.rate_limit, max_requests=args.max_requests, max_duration=args.max_duration, headers=_pairs(args.header, "header"), cookies=_pairs(args.cookie, "cookie"), proxy=args.proxy, allow_private=args.allow_private)
    try:
        graph = await discover(args.domain, config)
    except RuntimeError:
        if not args.recovery:
            raise
        words = (line.strip() for line in args.wordlist) if args.wordlist else ()
        graph = (await recover(args.domain, words, config)).graph
    for artifact in args.artifacts:
        graph.merge(parse_artifact(artifact))
    write(graph, args.output, args.format)
    logging.getLogger("cryql").info("wrote %s", args.output)


def main(argv: Optional[List[str]] = None) -> None:
    args = build_parser().parse_args(argv)
    logging.basicConfig(level=logging.DEBUG if args.debug else logging.INFO, format="%(levelname)s %(message)s")
    asyncio.run(run(args))
