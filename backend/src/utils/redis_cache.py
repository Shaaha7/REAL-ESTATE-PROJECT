"""
NEW UTIL: Redis Cache for RAG queries
Drop into: backend/src/utils/redis_cache.py
Caches frequent RAG answers so same question returns instantly.
Falls back gracefully if Redis not available.
"""
from __future__ import annotations
import json
import hashlib
from typing import Optional
from loguru import logger

class RAGCache:
    """
    Simple Redis cache for RAG query results.
    Falls back to in-memory dict if Redis unavailable.
    TTL: 1 hour for RAG answers (real estate facts don't change hourly)
    """
    def __init__(self, redis_url: str = "redis://localhost:6379", ttl: int = 3600):
        self.ttl = ttl
        self._redis = None
        self._memory_cache: dict = {}  # fallback

        try:
            import redis
            self._redis = redis.from_url(redis_url, decode_responses=True, socket_timeout=2)
            self._redis.ping()
            logger.info("Redis cache connected")
        except Exception as e:
            logger.warning(f"Redis unavailable ({e}). Using in-memory cache.")

    def _key(self, question: str) -> str:
        return f"rag:{hashlib.md5(question.lower().strip().encode()).hexdigest()}"

    def get(self, question: str) -> Optional[dict]:
        k = self._key(question)
        try:
            if self._redis:
                val = self._redis.get(k)
                if val:
                    logger.debug(f"Cache HIT: {question[:50]}")
                    return json.loads(val)
        except Exception:
            pass
        # fallback memory
        if k in self._memory_cache:
            logger.debug(f"Memory cache HIT: {question[:50]}")
            return self._memory_cache[k]
        return None

    def set(self, question: str, result: dict) -> None:
        k = self._key(question)
        serialized = json.dumps(result, default=str)
        try:
            if self._redis:
                self._redis.setex(k, self.ttl, serialized)
                return
        except Exception:
            pass
        # fallback memory (keep last 100)
        if len(self._memory_cache) >= 100:
            oldest = next(iter(self._memory_cache))
            del self._memory_cache[oldest]
        self._memory_cache[k] = result

    def clear(self) -> None:
        self._memory_cache.clear()
        try:
            if self._redis:
                keys = self._redis.keys("rag:*")
                if keys:
                    self._redis.delete(*keys)
        except Exception:
            pass
