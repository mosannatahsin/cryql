from __future__ import annotations

import json
from typing import Any, Dict, Iterable, Optional

from .models import Argument, Confidence, Evidence, Field, TypeNode, TypeRef


class SchemaGraph:
    """Evidence-preserving graph of recovered GraphQL schema elements."""

    def __init__(self) -> None:
        self.types: Dict[str, TypeNode] = {}
        self.relationships: Dict[str, str] = {}
        self.query_type: Optional[str] = None
        self.mutation_type: Optional[str] = None
        self.subscription_type: Optional[str] = None

    def add_type(self, node: TypeNode, evidence: Optional[Evidence] = None) -> TypeNode:
        current = self.types.get(node.name)
        if current is None:
            self.types[node.name] = node
            current = node
        elif current.kind != node.kind:
            current.confidence = Confidence.CONTRADICTED
        if evidence:
            current.evidence.append(evidence)
        return current

    def add_field(self, parent: str, field: Field, evidence: Optional[Evidence] = None) -> Field:
        node = self.types.setdefault(parent, TypeNode(parent, "OBJECT"))
        existing = node.fields.get(field.name)
        if existing and existing.type_ref != field.type_ref:
            if existing.type_ref.name is None and existing.type_ref.kind is None:
                existing.type_ref = field.type_ref
                existing.confidence = field.confidence
            else:
                existing.confidence = Confidence.CONTRADICTED
                existing.evidence.extend(field.evidence)
                return existing
        if existing is None:
            node.fields[field.name] = field
            existing = field
        else:
            known_args = {argument.name for argument in existing.args}
            existing.args.extend(argument for argument in field.args if argument.name not in known_args)
            if existing.confidence == Confidence.UNKNOWN and field.confidence != Confidence.UNKNOWN:
                existing.confidence = field.confidence
            existing.evidence.extend(field.evidence)
        if existing.type_ref.kind == "OBJECT" and existing.type_ref.name:
            self.relationships[f"{parent}.{field.name}"] = existing.type_ref.name
        if evidence:
            existing.evidence.append(evidence)
        return existing

    @classmethod
    def from_introspection(cls, payload: Dict[str, Any]) -> "SchemaGraph":
        schema = payload.get("data", {}).get("__schema", payload.get("__schema", payload))
        graph = cls()
        for root, attr in (("query_type", "queryType"), ("mutation_type", "mutationType"), ("subscription_type", "subscriptionType")):
            root_value = schema.get(attr) or {}
            setattr(graph, root, root_value.get("name"))
        for raw in schema.get("types", []):
            if not raw.get("name"):
                continue
            node = TypeNode(raw["name"], raw.get("kind", "UNKNOWN"), confidence=Confidence.CONFIRMED)
            for value in raw.get("enumValues") or []:
                node.enum_values.append(value["name"])
            for value in raw.get("possibleTypes") or []:
                node.possible_types.append(value["name"])
            for value in raw.get("inputFields") or []:
                node.input_fields[value["name"]] = Argument(value["name"], TypeRef.from_introspection(value["type"]), value.get("defaultValue"))
            for value in raw.get("fields") or []:
                args = [Argument(a["name"], TypeRef.from_introspection(a["type"]), a.get("defaultValue")) for a in value.get("args") or []]
                node.fields[value["name"]] = Field(value["name"], TypeRef.from_introspection(value["type"]), args, Confidence.CONFIRMED)
            graph.add_type(node, Evidence("introspection", "introspection", verified=True))
            for value in node.fields.values():
                if value.type_ref.kind == "OBJECT" and value.type_ref.name:
                    graph.relationships[f"{node.name}.{value.name}"] = value.type_ref.name
        return graph

    def to_introspection(self) -> Dict[str, Any]:
        def arg(value: Argument) -> Dict[str, Any]:
            return {"name": value.name, "description": None, "type": value.type_ref.to_introspection(), "defaultValue": value.default_value}
        types = []
        for node in self.types.values():
            fields = [{"name": f.name, "description": None, "args": [arg(a) for a in f.args], "type": f.type_ref.to_introspection(), "isDeprecated": False, "deprecationReason": None} for f in node.fields.values()]
            types.append({"kind": node.kind, "name": node.name, "description": None, "fields": fields or None, "inputFields": [arg(a) for a in node.input_fields.values()] or None, "interfaces": [], "enumValues": [{"name": v, "description": None, "isDeprecated": False, "deprecationReason": None} for v in node.enum_values] or None, "possibleTypes": [{"name": v} for v in node.possible_types] or None})
        return {"data": {"__schema": {"queryType": {"name": self.query_type} if self.query_type else None, "mutationType": {"name": self.mutation_type} if self.mutation_type else None, "subscriptionType": {"name": self.subscription_type} if self.subscription_type else None, "types": types, "directives": []}}}

    def to_sdl(self) -> str:
        lines = []
        for node in self.types.values():
            if node.kind == "SCALAR":
                lines.append(f"scalar {node.name}")
            elif node.kind == "ENUM":
                lines.append("enum %s {\n%s\n}" % (node.name, "\n".join(f"  {v}" for v in node.enum_values)))
            elif node.kind == "INPUT_OBJECT":
                lines.append("input %s {\n%s\n}" % (node.name, "\n".join(f"  {a.name}: {a.type_ref.to_sdl()}" for a in node.input_fields.values())))
            elif node.kind in ("OBJECT", "INTERFACE"):
                lines.append("%s %s {\n%s\n}" % (node.kind.lower(), node.name, "\n".join(f"  {f.name}({', '.join(a.name + ': ' + a.type_ref.to_sdl() for a in f.args)}): {f.type_ref.to_sdl()}" if f.args else f"  {f.name}: {f.type_ref.to_sdl()}" for f in node.fields.values())))
        return "\n\n".join(lines) + ("\n" if lines else "")

    def evidence_report(self) -> Dict[str, Any]:
        return {"query_type": self.query_type, "mutation_type": self.mutation_type, "subscription_type": self.subscription_type, "relationships": dict(self.relationships), "types": {name: node.as_dict() for name, node in self.types.items()}}

    def merge(self, other: "SchemaGraph") -> None:
        for node in other.types.values():
            current = self.add_type(node)
            for field in node.fields.values():
                self.add_field(current.name, field)
        self.relationships.update(other.relationships)
