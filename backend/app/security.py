"""Request security helpers.

Purpose: Provide lightweight per-client API rate limiting.
Callers: FastAPI route dependencies and handlers.
Deps: time, collections, FastAPI request and exception types.
API: RateLimiter.check(request).
Side effects: Stores in-memory request timestamps per client.
"""

import time
from collections import defaultdict, deque
from threading import Lock

from fastapi import HTTPException, Request, status


class RateLimiter:
    def __init__(self, limit_per_minute: int):
        self.limit = limit_per_minute
        self.requests: dict[str, deque[float]] = defaultdict(deque)
        self._lock = Lock()

    def check(self, request: Request) -> None:
        client = request.client.host if request.client else 'unknown'
        now = time.time()
        with self._lock:
            self._prune_expired(now)
            window = self.requests[client]
            if len(window) >= self.limit:
                raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail='Rate limit exceeded')
            window.append(now)

    def _prune_expired(self, now: float) -> None:
        expired_clients = []
        for client, window in self.requests.items():
            while window and now - window[0] > 60:
                window.popleft()
            if not window:
                expired_clients.append(client)
        for client in expired_clients:
            self.requests.pop(client, None)
