"""Lightweight per-API-key rate limiter for /api/v3.

Fixed-window counter keyed by `apikey:{id}:{window_start}`. Backs onto the
shared `cache` (Redis if available, in-memory otherwise).
"""
from __future__ import annotations

import logging
import os
import time
from typing import Callable

from fastapi import HTTPException, Request, status

logger = logging.getLogger(__name__)

RATE_LIMIT_READ = int(os.getenv("API_V3_RATE_READ_PER_MIN", "120"))
RATE_LIMIT_WRITE = int(os.getenv("API_V3_RATE_WRITE_PER_MIN", "60"))
RATE_LIMIT_BULK = int(os.getenv("API_V3_RATE_BULK_PER_MIN", "10"))

_WINDOW_SEC = 60


async def _incr(key: str, ttl: int) -> int:
    """Increment counter with TTL. Returns new value. Works with Redis or in-memory."""
    from web.backend.core.cache import cache
    # Redis path
    redis = getattr(cache, "_redis", None)
    if redis is not None:
        try:
            pipe = redis.pipeline()
            pipe.incr(key)
            pipe.expire(key, ttl)
            results = await pipe.execute()
            return int(results[0])
        except Exception as e:
            logger.debug("Redis INCR failed, falling back: %s", e)
    # In-memory fallback
    bucket = getattr(cache, "_memory", None) or {}
    now = time.time()
    entry = bucket.get(key)
    if not entry or entry[1] < now:
        bucket[key] = (1, now + ttl)
        if hasattr(cache, "_memory"):
            cache._memory = bucket
        return 1
    value, expires = entry
    value += 1
    bucket[key] = (value, expires)
    if hasattr(cache, "_memory"):
        cache._memory = bucket
    return value


def rate_limit(max_per_minute: int) -> Callable:
    """Dependency: enforces rate limit for the authenticated API key.

    Must be used AFTER require_api_key/require_scope on the same endpoint so
    that `request.state.api_key_user` is already set.
    """
    async def _dep(request: Request) -> None:
        user = getattr(request.state, "api_key_user", None)
        if user is None:
            # No key yet — let auth dep raise its own 401; skip limiting.
            return
        now = int(time.time())
        window = now - (now % _WINDOW_SEC)
        key = f"rl:apikey:{user.key_id}:{window}"
        try:
            count = await _incr(key, _WINDOW_SEC + 5)
        except Exception as e:
            logger.debug("Rate limit check skipped: %s", e)
            return
        if count > max_per_minute:
            retry_after = _WINDOW_SEC - (now - window)
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded: {max_per_minute} requests per minute",
                headers={"Retry-After": str(max(1, retry_after))},
            )

    return _dep


read_limit = rate_limit(RATE_LIMIT_READ)
write_limit = rate_limit(RATE_LIMIT_WRITE)
bulk_limit = rate_limit(RATE_LIMIT_BULK)
