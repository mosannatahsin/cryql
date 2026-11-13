from __future__ import annotations

import asyncio
import re
from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional, Tuple

from .config import CryQLConfig
from .models import Argument, Confidence, Evidence, Field, TypeNode, TypeRef
from .network import GraphQLClient
from .planner import AdaptivePlanner, Hypothesis
from .protocol import (
    GraphQLError,
    enum_values,
    parse_response,
    required_argument,
    required_input_field,
    suggestions,
)
from .schema import SchemaGraph


@dataclass(slots=True)
class RecoveryResult:
    graph: SchemaGraph
    requests: int
    errors: List[str] = field(default_factory=list)


def _selection_type(errors: Iterable[GraphQLError]) -> Optional[str]:
    for error in errors:
        match = re.search(r"""type ['"]([_A-Za-z][_0-9A-Za-z]*)['"]""", error.message)
        if match and ("selection" in error.message or "subfields" in error.message):
            return match.group(1)
    return None


def _type_ref(type_name: str) -> TypeRef:
    non_null = type_name.endswith("!")
    name = type_name.rstrip("!")
    if name in {"String", "Int", "Float", "Boolean", "ID"}:
        kind = "SCALAR"
    elif name.endswith(("Input", "Filter")):
        kind = "INPUT_OBJECT"
    else:
        kind = "UNKNOWN"
    base = TypeRef(name, kind)
    return TypeRef(None, "NON_NULL", base) if non_null else base


def _argument_value(type_name: str) -> str:
    name = type_name.rstrip("!")
    if name in {"Int", "Float"}:
        return "1"
    if name == "Boolean":
        return "true"
    if name.startswith("["):
        return "[]"
    if type_name.rstrip("!").endswith(("Input", "Filter")):
        return "{}"
    return '"x"'


def _document(path: Tuple[str, ...], arguments: Dict[Tuple[str, ...], Dict[str, str]]) -> str:
    if not path:
        raise ValueError("a GraphQL path cannot be empty")

    def selection(index: int, prefix: Tuple[str, ...]) -> str:
        field = path[index]
        args = arguments.get(prefix, {})
        suffix = f"({', '.join(f'{name}: {value}' for name, value in args.items())})" if args else ""
        rendered = field + suffix
        if index + 1 < len(path):
            rendered += " { " + selection(index + 1, prefix + (field,)) + " }"
        return rendered

    return "query { " + selection(0, (path[0],)) + " }"


async def recover(
    url: str,
    words: Iterable[str],
    config: Optional[CryQLConfig] = None,
    root_type: str = "Query",
) -> RecoveryResult:
    """Recover fields and required arguments using bounded validation evidence."""
    config = config or CryQLConfig()
    word_list = list(dict.fromkeys(word for word in words if word))
    graph = SchemaGraph()
    graph.query_type = root_type
    graph.add_type(TypeNode(root_type, "OBJECT", confidence=Confidence.CONFIRMED))
    planner = AdaptivePlanner(config.max_requests)
    queue: List[Tuple[str, Tuple[str, ...]]] = [(root_type, (word,)) for word in word_list]
    arguments: Dict[Tuple[str, ...], Dict[str, str]] = {}
    argument_types: Dict[Tuple[str, ...], Dict[str, str]] = {}
    seen_paths: set[Tuple[str, ...]] = set()
    errors: List[str] = []

    async with GraphQLClient(url, config) as client:
        while queue:
            parent_type, path = queue.pop(0)
            if path in seen_paths:
                continue
            seen_paths.add(path)
            document = _document(path, arguments)
            hypothesis = Hypothesis(document, "validation candidate", 1.0)
            if not planner.accept(hypothesis):
                continue
            try:
                payload = await client.execute(document)
            except RuntimeError as error:
                errors.append(str(error))
                break
            data, response_errors = parse_response(payload)
            field_name = path[-1]
            evidence = Evidence(url, "validation", document, verified=True)
            if not response_errors:
                value = data
                for part in path:
                    value = value.get(part) if isinstance(value, dict) else None
                type_ref = TypeRef("String", "SCALAR") if isinstance(value, str) else TypeRef(None, None)
                graph.add_field(parent_type, Field(field_name, type_ref, confidence=Confidence.STRONGLY_INFERRED, evidence=[evidence]))
                continue

            required = next((required_argument(error.message) for error in response_errors if required_argument(error.message)), None)
            if required:
                argument_name, type_name = required
                prefix = path
                arguments.setdefault(prefix, {})[argument_name] = _argument_value(type_name)
                argument_types.setdefault(prefix, {})[argument_name] = type_name
                graph.add_field(parent_type, Field(field_name, TypeRef(None, None), [Argument(argument_name, _type_ref(type_name), evidence=[evidence])], Confidence.INFERRED, [evidence]))
                seen_paths.discard(path)
                queue.insert(0, (parent_type, path))
                continue

            input_field = next((required_input_field(error.message) for error in response_errors if required_input_field(error.message)), None)
            if input_field:
                input_name, input_type = input_field
                input_type_name = next(iter(argument_types.get(path, {}).values()), "Input")
                input_node = graph.add_type(TypeNode(input_type_name.rstrip("!"), "INPUT_OBJECT", confidence=Confidence.INFERRED), evidence)
                input_node.input_fields[input_name] = Argument(input_name, _type_ref(input_type), evidence=[evidence])
                argument_name = next(iter(argument_types.get(path, {})), None)
                if argument_name:
                    arguments[path][argument_name] = "{ " + input_name + ": " + _argument_value(input_type) + " }"
                    seen_paths.discard(path)
                    queue.insert(0, (parent_type, path))
                continue

            enum_observation = next((enum_values(error.message) for error in response_errors if enum_values(error.message)), None)
            if enum_observation:
                enum_name, values = enum_observation
                enum_node = graph.add_type(TypeNode(enum_name, "ENUM", confidence=Confidence.INFERRED), evidence)
                for value in values:
                    if value not in enum_node.enum_values:
                        enum_node.enum_values.append(value)
                continue

            selected = _selection_type(response_errors)
            if selected:
                graph.add_type(TypeNode(selected, "OBJECT", confidence=Confidence.INFERRED), evidence)
                graph.add_field(parent_type, Field(field_name, TypeRef(selected, "OBJECT"), confidence=Confidence.STRONGLY_INFERRED, evidence=[evidence]))
                if len(path) == 1:
                    child_path = (field_name,)
                else:
                    child_path = path
                for child in word_list:
                    queue.append((selected, child_path + (child,)))
                continue

            for error in response_errors:
                for suggestion in suggestions(error.message):
                    graph.add_field(parent_type, Field(suggestion, TypeRef(None, None), confidence=Confidence.CANDIDATE, evidence=[Evidence(url, "suggestion", error.message)]))

    return RecoveryResult(graph, client.requests, errors)


def recover_sync(url: str, words: Iterable[str], config: Optional[CryQLConfig] = None) -> RecoveryResult:
    return asyncio.run(recover(url, words, config))
