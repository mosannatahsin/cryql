from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Optional


@dataclass(slots=True)
class CryQLConfig:
    """Bounded execution settings shared by the CLI and orchestrator."""

    timeout: float = 10.0
    retries: int = 2
    concurrency: int = 10
    rate_limit: float = 5.0
    max_requests: int = 100
    max_duration: float = 120.0
    max_response_size: int = 5 * 1024 * 1024
    allow_private: bool = False
    verify_tls: bool = True
    headers: Dict[str, str] = field(default_factory=dict)
    cookies: Dict[str, str] = field(default_factory=dict)
    proxy: Optional[str] = None

    def __post_init__(self) -> None:
        if self.timeout <= 0 or self.max_duration <= 0:
            raise ValueError("timeout and max_duration must be positive")
        if self.concurrency < 1 or self.max_requests < 1:
            raise ValueError("concurrency and max_requests must be positive")
        if self.retries < 0 or self.rate_limit < 0:
            raise ValueError("retries and rate_limit cannot be negative")
