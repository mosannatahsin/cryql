from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class Confidence(str, Enum):
    CONFIRMED = "CONFIRMED"
    STRONGLY_INFERRED = "STRONGLY_INFERRED"
    INFERRED = "INFERRED"
    CANDIDATE = "CANDIDATE"
    UNKNOWN = "UNKNOWN"
    CONTRADICTED = "CONTRADICTED"


@dataclass(frozen=True, slots=True)
class TypeRef:
    name: Optional[str] = None
    kind: Optional[str] = None
    of_type: Optional["TypeRef"] = None

    @classmethod
    def from_introspection(cls, value: Dict[str, Any]) -> "TypeRef":
        return cls(value.get("name"), value.get("kind"), cls.from_introspection(value["ofType"]) if value.get("ofType") else None)

    def to_introspection(self) -> Dict[str, Any]:
        return {"kind": self.kind, "name": self.name, "ofType": self.of_type.to_introspection() if self.of_type else None}

    def to_sdl(self) -> str:
        if self.kind == "NON_NULL":
            return f"{self.of_type.to_sdl()}!" if self.of_type else "!"
        if self.kind == "LIST":
            return f"[{self.of_type.to_sdl()}]" if self.of_type else "[]"
        return self.name or "Unknown"


@dataclass(slots=True)
class Evidence:
    source: str
    method: str
    detail: str = ""
    verified: bool = False
    timestamp: Optional[str] = None


@dataclass(slots=True)
class Argument:
    name: str
    type_ref: TypeRef
    default_value: Any = None
    evidence: List[Evidence] = field(default_factory=list)


@dataclass(slots=True)
class Field:
    name: str
    type_ref: TypeRef
    args: List[Argument] = field(default_factory=list)
    confidence: Confidence = Confidence.UNKNOWN
    evidence: List[Evidence] = field(default_factory=list)


@dataclass(slots=True)
class TypeNode:
    name: str
    kind: str
    fields: Dict[str, Field] = field(default_factory=dict)
    input_fields: Dict[str, Argument] = field(default_factory=dict)
    enum_values: List[str] = field(default_factory=list)
    possible_types: List[str] = field(default_factory=list)
    confidence: Confidence = Confidence.UNKNOWN
    evidence: List[Evidence] = field(default_factory=list)

    def as_dict(self) -> Dict[str, Any]:
        return asdict(self)
