from __future__ import annotations

import json
import asyncio
from typing import Any, Optional

import redis.asyncio as redis

from ..config import get_settings


class CacheService:
    def __init__(self) -> None:
        settings = get_settings()
        self.client = redis.from_url(settings.redis_url, decode_responses=True)

    async def get_json(self, key: str) -> Optional[Any]:
        raw = await self.client.get(key)
        if raw is None:
            return None
        try:
            return json.loads(raw)
        except Exception:
            return None

    async def set_json(self, key: str, value: Any, ttl_seconds: int | None = None) -> None:
        raw = json.dumps(value)
        if ttl_seconds:
            await self.client.setex(key, ttl_seconds, raw)
        else:
            await self.client.set(key, raw)

    async def delete(self, key: str) -> None:
        await self.client.delete(key)


_cache: CacheService | None = None


def get_cache() -> CacheService:
    global _cache
    if _cache is None:
        _cache = CacheService()
    return _cache
