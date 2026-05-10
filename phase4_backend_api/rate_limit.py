"""
Phase 5: Simple in-memory per-IP rate limiting middleware.

Goal: avoid external dependencies while meeting "30 requests/min per IP" requirement.
Note: In-memory limiter resets on process restart and is per-instance (fine for MVP).
"""

from __future__ import annotations

import time
from collections import deque
from dataclasses import dataclass
from typing import Deque, Dict

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response


@dataclass
class _Bucket:
    timestamps: Deque[float]


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, requests_per_minute: int = 30):
        super().__init__(app)
        self.requests_per_minute = max(1, requests_per_minute)
        self.window_seconds = 60.0
        self._by_ip: Dict[str, _Bucket] = {}

    def _client_ip(self, request: Request) -> str:
        # If behind a proxy/CDN, configure proper forwarded headers at the platform level.
        if request.client and request.client.host:
            return request.client.host
        return "unknown"

    async def dispatch(self, request: Request, call_next) -> Response:
        ip = self._client_ip(request)
        now = time.time()

        bucket = self._by_ip.get(ip)
        if bucket is None:
            bucket = _Bucket(timestamps=deque())
            self._by_ip[ip] = bucket

        # Evict old timestamps outside window
        cutoff = now - self.window_seconds
        while bucket.timestamps and bucket.timestamps[0] < cutoff:
            bucket.timestamps.popleft()

        if len(bucket.timestamps) >= self.requests_per_minute:
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded. Please try again later."},
            )

        bucket.timestamps.append(now)
        return await call_next(request)

