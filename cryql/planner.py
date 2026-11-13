from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Set


@dataclass(frozen=True, slots=True)
class Hypothesis:
    query: str
    reason: str
    expected_gain: float
    cost: float = 1.0

    @property
    def score(self) -> float:
        return self.expected_gain / max(self.cost, 0.1)


class AdaptivePlanner:
    """Deterministic, explainable prioritization; scores are not probabilities."""

    def __init__(self, max_requests: int) -> None:
        self.max_requests = max_requests
        self.seen: Set[str] = set()

    def prioritize(self, hypotheses: Iterable[Hypothesis]) -> List[Hypothesis]:
        fresh = [h for h in hypotheses if h.query not in self.seen]
        return sorted(fresh, key=lambda h: (-h.score, h.cost, h.query))

    def accept(self, hypothesis: Hypothesis) -> bool:
        if len(self.seen) >= self.max_requests or hypothesis.query in self.seen:
            return False
        self.seen.add(hypothesis.query)
        return True
