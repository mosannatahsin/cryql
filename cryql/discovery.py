from __future__ import annotations

from urllib.parse import urljoin, urlparse

from .network import SafetyError, validate_target


DEFAULT_PATHS = ("/graphql", "/api/graphql", "/graphql/")


def candidate_endpoints(target: str) -> list[str]:
    """Return conservative candidates without probing or crossing hosts."""
    parsed = urlparse(validate_target(target))
    base = f"{parsed.scheme}://{parsed.netloc}"
    path = parsed.path or "/"
    candidates = [target]
    if path == "/":
        candidates.extend(urljoin(base, item) for item in DEFAULT_PATHS)
    return list(dict.fromkeys(candidates))


def validate_candidates(targets: list[str], allow_private: bool = False) -> list[str]:
    origin = urlparse(validate_target(targets[0], allow_private)).netloc if targets else None
    valid = []
    for target in targets:
        checked = validate_target(target, allow_private)
        if urlparse(checked).netloc != origin:
            raise SafetyError("endpoint candidates must stay on the supplied host")
        valid.append(checked)
    return valid
