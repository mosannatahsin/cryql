import asyncio
import threading

from http.server import ThreadingHTTPServer

from cryql.config import CryQLConfig
from cryql.recovery import recover
from lab.server import Handler


def test_recovery_against_introspection_disabled_lab():
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    Handler.introspection = False
    Handler.suggestions = True
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        result = asyncio.run(
            recover(
                f"http://127.0.0.1:{server.server_port}/graphql",
                ["user", "health", "id", "name", "search", "status", "missing"],
                CryQLConfig(allow_private=True, rate_limit=0, max_requests=20),
            )
        )
        assert {"user", "health"} <= set(result.graph.types["Query"].fields)
        assert {"id", "name"} <= set(result.graph.types["User"].fields)
        assert result.graph.types["Query"].fields["user"].args[0].name == "id"
        assert result.graph.relationships["Query.user"] == "User"
        assert set(result.graph.types["Status"].enum_values) == {"ACTIVE", "INACTIVE"}
        assert result.graph.types["SearchFilter"].input_fields["term"].type_ref.of_type.name == "String"
    finally:
        server.shutdown()
        thread.join(timeout=2)
