import json
import re
import subprocess
import sys
from pathlib import Path

from cryql.artifacts import extract_operations
from cryql.discovery import candidate_endpoints, validate_candidates
from cryql.models import Confidence, Field, TypeRef
from cryql.network import SafetyError
from cryql.protocol import GraphQLError, enum_values, required_input_field, suggestions
from cryql.recovery import _selection_type
from cryql.export import render
from cryql.planner import AdaptivePlanner, Hypothesis
from cryql.schema import SchemaGraph


def test_module_entrypoint_displays_help():
    result = subprocess.run(
        [sys.executable, "-m", "cryql", "--help"],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "Evidence-driven GraphQL schema intelligence" in result.stdout


def test_packaging_declares_supported_python_range():
    pyproject = Path(__file__).parents[1] / "pyproject.toml"
    content = pyproject.read_text(encoding="utf-8")
    assert re.search(r'^python\s*=\s*">=3\.10,<4\.0"$', content, re.MULTILINE)


def test_introspection_graph_and_sdl():
    graph = SchemaGraph.from_introspection({"data": {"__schema": {"queryType": {"name": "Query"}, "mutationType": None, "subscriptionType": None, "types": [{"name": "Query", "kind": "OBJECT", "fields": [{"name": "user", "args": [], "type": {"kind": "SCALAR", "name": "String", "ofType": None}}]}]}}})
    assert graph.types["Query"].fields["user"].confidence is Confidence.CONFIRMED
    assert "type query" not in graph.to_sdl()
    assert "user: String" in graph.to_sdl()


def test_artifacts_remain_candidates():
    graph = extract_operations("query GetUser { user(id: 1) { id } }", "fixture.graphql")
    assert graph.types["Query"].fields["user"].confidence is Confidence.CANDIDATE


def test_planner_deduplicates_and_prioritizes():
    planner = AdaptivePlanner(2)
    items = planner.prioritize([Hypothesis("a", "x", 1), Hypothesis("b", "x", 2)])
    assert items[0].query == "b"
    assert planner.accept(items[0])
    assert not planner.accept(items[0])


def test_endpoint_candidates_are_same_origin():
    assert candidate_endpoints("https://example.test") == [
        "https://example.test",
        "https://example.test/graphql",
        "https://example.test/api/graphql",
        "https://example.test/graphql/",
    ]
    assert validate_candidates(["https://example.test/graphql"], False)
    try:
        validate_candidates(["https://example.test/graphql", "https://other.test/graphql"])
    except SafetyError:
        pass
    else:
        raise AssertionError("cross-origin candidate was accepted")


def test_validation_helpers_keep_suggestions_unverified():
    assert suggestions('Did you mean "user" or "health"?') == {"user", "health"}
    assert _selection_type([GraphQLError('Field "user" of type "User" must have a selection of subfields.')]) == "User"
    assert enum_values('Enum "Status" cannot represent non-enum value: "UNKNOWN". Did you mean "ACTIVE" or "INACTIVE"?') == ("Status", {"ACTIVE", "INACTIVE"})
    assert required_input_field('Field "term" of required type "String!" was not provided.') == ("term", "String!")


def test_evidence_export_is_json():
    graph = extract_operations("query { user }")
    report = json.loads(render(graph, "evidence"))
    assert report["types"]["Query"]["fields"]["user"]["confidence"] == "CANDIDATE"


def test_abstract_type_possible_types_are_preserved():
    graph = SchemaGraph.from_introspection(
        {
            "data": {
                "__schema": {
                    "queryType": {"name": "Query"},
                    "mutationType": None,
                    "subscriptionType": None,
                    "types": [
                        {
                            "name": "Node",
                            "kind": "INTERFACE",
                            "fields": [],
                            "possibleTypes": [{"name": "User"}],
                        }
                    ],
                }
            }
        }
    )
    assert graph.types["Node"].possible_types == ["User"]


def test_verified_object_field_is_recorded_as_relationship():
    graph = SchemaGraph()
    graph.add_field("Query", Field("user", TypeRef("User", "OBJECT"), confidence=Confidence.CONFIRMED))
    assert graph.relationships == {"Query.user": "User"}
