import hashlib
import hmac
import time
from collections import deque
from typing import Deque

from fastapi import HTTPException, Request, status

from app.core.config import get_settings


class RateLimiter:
    def __init__(self, limit_per_minute: int) -> None:
        self.limit_per_minute = limit_per_minute
        self._hits: dict[str, Deque[float]] = {}

    def check(self, key: str) -> None:
        now = time.time()
        window = self._hits.setdefault(key, deque())
        while window and now - window[0] > 60:
            window.popleft()
        if len(window) >= self.limit_per_minute:
            raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Rate limit exceeded")
        window.append(now)


rate_limiter = RateLimiter(get_settings().api_rate_limit_per_minute)


def mask_secret(value: str) -> str:
    if len(value) <= 4:
        return "****"
    return f"{value[:2]}***{value[-2:]}"


def verify_meta_signature(signature_header: str | None, body: bytes) -> bool:
    secret = get_settings().meta_app_secret
    if not secret:
        return True
    if not signature_header or not signature_header.startswith("sha256="):
        return False
    expected = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
    provided = signature_header.split("=", 1)[1]
    return hmac.compare_digest(expected, provided)


async def enforce_internal_rate_limit(request: Request) -> None:
    client = request.client.host if request.client else "unknown"
    rate_limiter.check(client)
