from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Set

NAME = re.compile(r"[_A-Za-z][_0-9A-Za-z]*")


@dataclass(frozen=True, slots=True)
class GraphQLError:
    message: str
    path: tuple[Any, ...] = ()
    locations: tuple[Dict[str, int], ...] = ()


def parse_response(payload: Any) -> tuple[Dict[str, Any], List[GraphQLError]]:
    if not isinstance(payload, dict):
        raise ValueError("GraphQL response must be a JSON object")
    errors = [GraphQLError(e.get("message", ""), tuple(e.get("path") or ()), tuple(e.get("locations") or ())) for e in payload.get("errors", []) if isinstance(e, dict)]
    return payload.get("data") or {}, errors


def suggestions(message: str) -> Set[str]:
    return set(re.findall(r"""['"]([_A-Za-z][_0-9A-Za-z]*)['"]""", message.split("Did you mean", 1)[-1] if "Did you mean" in message else ""))


def referenced_type(message: str) -> str | None:
    match = re.search(r"""(?:type|Expected type) ['"]?([_A-Za-z][_0-9A-Za-z]*)!?['"]?""", message)
    return match.group(1) if match else None


def required_argument(message: str) -> tuple[str, str] | None:
    match = re.search(
        r"""Field ['"]([_A-Za-z][_0-9A-Za-z]*)['"] argument ['"]([_A-Za-z][_0-9A-Za-z]*)['"] of type ['"]([^'"]+)['"] is required""",
        message,
    )
    return (match.group(2), match.group(3)) if match else None


def enum_values(message: str) -> tuple[str, Set[str]] | None:
    type_match = re.search(r"""(?:Enum ['"]|in ['"])([_A-Za-z][_0-9A-Za-z]*)['"]""", message)
    if not type_match:
        return None
    value_text = message.split("Did you mean", 1)[-1] if "Did you mean" in message else ""
    values = set(re.findall(r"""['"]([_A-Za-z][_0-9A-Za-z]*)['"]""", value_text))
    return type_match.group(1), values


def required_input_field(message: str) -> tuple[str, str] | None:
    match = re.search(
        r"""Field ['"]([_A-Za-z][_0-9A-Za-z]*)['"] of required type ['"]([^'"]+)['"] was not provided""",
        message,
    )
    return (match.group(1), match.group(2)) if match else None


def is_introspection_denied(errors: Iterable[GraphQLError]) -> bool:
    terms = ("introspection", "__schema", "__type", "not allowed")
    return any(any(term in error.message.lower() for term in terms) for error in errors)
