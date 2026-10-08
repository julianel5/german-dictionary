"""Optional Redis-backed response cache.

Disabled unless both ``REDIS_URL`` and a positive ``CACHE_TTL_SECONDS``
are configured. Any Redis failure degrades to "cache off" — search must
never depend on the cache being reachable.
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


class ResponseCache:
    def __init__(self, redis_url: str | None, ttl_seconds: int) -> None:
        self._redis_url = redis_url
        self._ttl = ttl_seconds
        self._client = None
        self._broken = False

    @property
    def enabled(self) -> bool:
        return bool(self._redis_url) and self._ttl > 0 and not self._broken

    def _redis(self):  # type: ignore[no-untyped-def]
        if self._client is None and self._redis_url:
            import redis

            self._client = redis.Redis.from_url(self._redis_url, decode_responses=True)
        return self._client

    def get(self, key: str) -> str | None:
        if not self.enabled:
            return None
        try:
            value = self._redis().get(key)
        except Exception as exc:
            self._mark_broken("get", exc)
            return None
        return value if isinstance(value, str) else None

    def set(self, key: str, value: str) -> None:
        if not self.enabled:
            return
        try:
            self._redis().set(key, value, ex=self._ttl)
        except Exception as exc:
            self._mark_broken("set", exc)

    def ping(self) -> bool:
        if not self.enabled:
            return False
        try:
            return bool(self._redis().ping())
        except Exception:
            return False

    def _mark_broken(self, operation: str, exc: Exception) -> None:
        self._broken = True
        logger.warning("redis %s failed (%s); response cache disabled", operation, exc)
