from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List

from .models import Argument, Confidence, Evidence, Field, TypeNode, TypeRef
from .schema import SchemaGraph


NAME = r"[_A-Za-z][_0-9A-Za-z]*"


def extract_operations(text: str, source: str = "artifact") -> SchemaGraph:
    graph = SchemaGraph()
    evidence = Evidence(source, "artifact", verified=False)
    for match in re.finditer(r"\b(?:query|mutation|subscription)\s*(\w+)?\s*\{([^{}]*)", text, re.S):
        body = match.group(2)
        root = "Query" if match.group(0).lstrip().startswith("query") else "Mutation" if match.group(0).lstrip().startswith("mutation") else "Subscription"
        setattr(graph, root.lower() + "_type", root)
        graph.add_type(TypeNode(root, "OBJECT", confidence=Confidence.CANDIDATE), evidence)
        for field in re.findall(rf"\b({NAME})\s*(?:\(([^)]*)\))?", body):
            args = []
            if field[1]:
                for arg in re.findall(rf"({NAME})\s*:", field[1]):
                    args.append(Argument(arg, TypeRef("String", "SCALAR")))
            graph.add_field(root, Field(field[0], TypeRef(None, None), args, Confidence.CANDIDATE, [evidence]))
    return graph


def parse_artifact(path: str) -> SchemaGraph:
    file = Path(path)
    if file.stat().st_size > 10 * 1024 * 1024:
        raise ValueError("artifact exceeds the 10 MiB safety limit")
    text = file.read_text(encoding="utf-8", errors="replace")
    if file.suffix.lower() == ".json":
        payload = json.loads(text)
        if isinstance(payload, dict) and ("log" in payload or "entries" in payload):
            text = json.dumps(payload)
        elif isinstance(payload, dict) and "data" in payload:
            return SchemaGraph.from_introspection(payload)
    return extract_operations(text, str(file))
