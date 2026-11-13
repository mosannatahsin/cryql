from __future__ import annotations

import asyncio
from typing import Optional

from .config import CryQLConfig
from .models import Evidence
from .network import GraphQLClient
from .protocol import parse_response
from .schema import SchemaGraph

INTROSPECTION = """query CryQLIntrospection { __schema { queryType { name } mutationType { name } subscriptionType { name } types { kind name enumValues { name } possibleTypes { name } fields(includeDeprecated: true) { name args { name type { ...TypeRef } defaultValue } type { ...TypeRef } } inputFields { name type { ...TypeRef } defaultValue } } } } fragment TypeRef on __Type { kind name ofType { kind name ofType { kind name ofType { kind name ofType { kind name } } } } }"""


async def discover(url: str, config: Optional[CryQLConfig] = None) -> SchemaGraph:
    config = config or CryQLConfig()
    async with GraphQLClient(url, config) as client:
        payload = await client.execute(INTROSPECTION)
    data, errors = parse_response(payload)
    if not data.get("__schema"):
        detail = "; ".join(error.message for error in errors) or "introspection returned no schema"
        raise RuntimeError(detail)
    graph = SchemaGraph.from_introspection({"data": data})
    for node in graph.types.values():
        node.evidence.append(Evidence(url, "introspection", verified=True))
    return graph


def discover_sync(url: str, config: Optional[CryQLConfig] = None) -> SchemaGraph:
    return asyncio.run(discover(url, config))
