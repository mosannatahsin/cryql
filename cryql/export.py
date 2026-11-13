from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .schema import SchemaGraph


def render(graph: SchemaGraph, fmt: str) -> str:
    if fmt == "json":
        return json.dumps(graph.to_introspection(), indent=2, sort_keys=True) + "\n"
    if fmt == "sdl":
        return graph.to_sdl()
    if fmt == "evidence":
        return json.dumps(graph.evidence_report(), indent=2, sort_keys=True, default=str) + "\n"
    raise ValueError(f"unsupported output format: {fmt}")


def write(graph: SchemaGraph, path: str, fmt: str) -> None:
    Path(path).write_text(render(graph, fmt), encoding="utf-8")
