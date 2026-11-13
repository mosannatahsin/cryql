from __future__ import annotations

import asyncio
import time
from collections import deque
from typing import Any, Dict, Optional
from urllib.parse import urlparse
import ipaddress

import aiohttp

from .config import CryQLConfig


class SafetyError(ValueError):
    pass


def validate_target(url: str, allow_private: bool = False) -> str:
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        raise SafetyError("target must be an absolute HTTP(S) URL")
    host = parsed.hostname
    if not host:
        raise SafetyError("target hostname is missing")
    try:
        address = ipaddress.ip_address(host)
        private = address.is_private or address.is_loopback or address.is_link_local
    except ValueError:
        private = host.lower() in ("localhost",)
    if private and not allow_private:
        raise SafetyError("private and loopback targets are disabled by default")
    return url


class RateLimiter:
    def __init__(self, rate: float) -> None:
        self.rate = rate
        self._last = 0.0
        self._lock = asyncio.Lock()

    async def wait(self) -> None:
        if self.rate <= 0:
            return
        async with self._lock:
            delay = 1 / self.rate - (time.monotonic() - self._last)
            if delay > 0:
                await asyncio.sleep(delay)
            self._last = time.monotonic()


class GraphQLClient:
    def __init__(self, url: str, config: CryQLConfig) -> None:
        self.url = validate_target(url, config.allow_private)
        self.config = config
        self.limiter = RateLimiter(config.rate_limit)
        self.requests = 0
        self.started = time.monotonic()
        self._semaphore = asyncio.Semaphore(config.concurrency)
        self._session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self) -> "GraphQLClient":
        timeout = aiohttp.ClientTimeout(total=self.config.timeout)
        headers = dict(self.config.headers)
        if self.config.cookies:
            headers["Cookie"] = "; ".join(f"{k}={v}" for k, v in self.config.cookies.items())
        self._session = aiohttp.ClientSession(timeout=timeout, headers=headers)
        return self

    async def __aexit__(self, *_: Any) -> None:
        if self._session:
            await self._session.close()

    async def execute(self, query: str, variables: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        if self.requests >= self.config.max_requests:
            raise RuntimeError("maximum request budget exceeded")
        if time.monotonic() - self.started >= self.config.max_duration:
            raise RuntimeError("maximum duration exceeded")
        if not self._session:
            raise RuntimeError("client must be used as an async context manager")
        async with self._semaphore:
            await self.limiter.wait()
            self.requests += 1
            for attempt in range(self.config.retries + 1):
                try:
                    async with self._session.post(self.url, json={"query": query, "variables": variables or {}}, proxy=self.config.proxy, ssl=self.config.verify_tls) as response:
                        body = await response.content.read(self.config.max_response_size + 1)
                        if len(body) > self.config.max_response_size:
                            raise RuntimeError("response size limit exceeded")
                        if response.status >= 500 and attempt < self.config.retries:
                            await asyncio.sleep(min(2**attempt, 8))
                            continue
                        if response.status >= 400:
                            raise RuntimeError(f"HTTP {response.status}")
                        import json
                        return json.loads(body.decode(response.charset or "utf-8"))
                except (aiohttp.ClientError, asyncio.TimeoutError) as exc:
                    if attempt >= self.config.retries:
                        raise RuntimeError(f"GraphQL request failed: {exc}") from exc
                    await asyncio.sleep(min(2**attempt, 8))
        raise RuntimeError("request failed")
