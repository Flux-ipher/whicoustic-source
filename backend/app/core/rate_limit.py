"""
Rate limiting and in-memory caching engine for Whicoustic API.
Implements Token Bucket, Leaky Token Bucket algorithms, and TTL Memory Cache
to protect synthesis, cloning, and audio streaming endpoints from API abuse.

Hardened with:
- Monotonic clock (time.monotonic()) evaluated inside mutex locks.
- Strict timestamp inversion and clock drift protection via max(last_ts, now).
- Automatic backward compatibility normalization for legacy epoch timestamps in _buckets.
- Idle bucket TTL eviction (cleanup()) and unbounded IP flood capping (max_buckets).
- Accurate MemoryCache.has() handling for None values.
"""

from __future__ import annotations

import time
import threading
from typing import Dict, Tuple, Optional, Any
from fastapi import Request, HTTPException, status


class TokenBucketRateLimiter:
    """
    Token Bucket rate limiter algorithm.
    Allows bursts up to `capacity` tokens while replenishing at a steady `refill_rate` (tokens/second).
    Synchronized with re-entrant/mutex locking, monotonic time tracking, and idle bucket eviction.
    """

    def __init__(
        self,
        capacity: float = 10.0,
        refill_rate: float = 2.0,
        max_idle: float = 3600.0,
        cleanup_interval: float = 300.0,
        max_buckets: int = 50000,
    ):
        self.capacity = float(capacity)
        self.refill_rate = float(refill_rate)
        self.max_idle = float(max_idle)
        self.cleanup_interval = float(cleanup_interval)
        self.max_buckets = int(max_buckets)
        # key -> (current_tokens, last_refill_timestamp)
        self._buckets: Dict[str, Tuple[float, float]] = {}
        self._last_cleanup = time.monotonic()
        self._lock = threading.Lock()

    def acquire(self, key: str, tokens: float = 1.0) -> bool:
        """Attempt to consume `tokens` for the specified key. Returns True if granted, False if rate limited."""
        with self._lock:
            now = time.monotonic()
            self._maybe_cleanup(now)

            if key not in self._buckets:
                current_tokens = self.capacity
                last_refill = now
            else:
                current_tokens, last_refill = self._buckets[key]
                # Epoch normalization guard: if a legacy test/harness injected time.time() (> 1e8)
                # while monotonic clock is < 1e8, normalize timestamp to prevent permanent token freeze
                if last_refill > 1e8 and now < 1e8:
                    elapsed = 0.0
                    last_refill = now
                else:
                    elapsed = max(0.0, now - last_refill)
                    last_refill = max(last_refill, now)
                current_tokens = min(self.capacity, current_tokens + elapsed * self.refill_rate)

            if current_tokens >= tokens:
                self._buckets[key] = (current_tokens - tokens, last_refill)
                return True
            else:
                self._buckets[key] = (current_tokens, last_refill)
                return False

    def get_wait_time(self, key: str, tokens: float = 1.0) -> float:
        """Return the estimated seconds until enough tokens are replenished."""
        with self._lock:
            now = time.monotonic()
            if key not in self._buckets:
                return 0.0
            current_tokens, last_refill = self._buckets[key]
            if last_refill > 1e8 and now < 1e8:
                elapsed = 0.0
            else:
                elapsed = max(0.0, now - last_refill)
            current_tokens = min(self.capacity, current_tokens + elapsed * self.refill_rate)
            if current_tokens >= tokens:
                return 0.0
            needed = tokens - current_tokens
            return needed / self.refill_rate if self.refill_rate > 0 else 0.0

    def cleanup(self, max_idle: Optional[float] = None) -> int:
        """
        Purge idle client buckets that have not had requests for >= `max_idle` seconds.
        Returns the count of purged buckets.
        """
        effective_idle = float(max_idle) if max_idle is not None else self.max_idle
        with self._lock:
            now = time.monotonic()
            self._last_cleanup = now
            stale_keys = [
                k for k, (_, last_seen) in self._buckets.items()
                if (now - last_seen) >= effective_idle
            ]
            for k in stale_keys:
                del self._buckets[k]
            return len(stale_keys)

    def _maybe_cleanup(self, now: float) -> None:
        """Passive opportunistic eviction of stale buckets."""
        if (now - self._last_cleanup) >= self.cleanup_interval or len(self._buckets) >= self.max_buckets:
            self._last_cleanup = now
            stale_keys = [
                k for k, (_, last_seen) in self._buckets.items()
                if (now - last_seen) >= self.max_idle
            ]
            for k in stale_keys:
                del self._buckets[k]

            # If still saturated beyond capacity under active IP spoofing DDoS, evict oldest entries
            if len(self._buckets) >= self.max_buckets:
                excess = len(self._buckets) - self.max_buckets + 1
                oldest_keys = sorted(self._buckets.keys(), key=lambda k: self._buckets[k][1])[:excess]
                for k in oldest_keys:
                    del self._buckets[k]

    def reset(self, key: Optional[str] = None):
        """Reset rate limiter state for a key or globally."""
        with self._lock:
            if key:
                self._buckets.pop(key, None)
            else:
                self._buckets.clear()


class LeakyBucketRateLimiter:
    """
    Leaky Bucket rate limiter algorithm.
    Enforces a constant outflow leak rate and rejects requests when the bucket overflows capacity.
    Synchronized with re-entrant/mutex locking, monotonic time tracking, and idle bucket eviction.
    """

    def __init__(
        self,
        capacity: float = 20.0,
        leak_rate: float = 5.0,
        max_idle: float = 3600.0,
        cleanup_interval: float = 300.0,
        max_buckets: int = 50000,
    ):
        self.capacity = float(capacity)
        self.leak_rate = float(leak_rate)
        self.max_idle = float(max_idle)
        self.cleanup_interval = float(cleanup_interval)
        self.max_buckets = int(max_buckets)
        # key -> (current_water_level, last_leak_timestamp)
        self._buckets: Dict[str, Tuple[float, float]] = {}
        self._last_cleanup = time.monotonic()
        self._lock = threading.Lock()

    def acquire(self, key: str, amount: float = 1.0) -> bool:
        """Attempt to add `amount` of water into the bucket. Returns True if accepted, False if overflowed."""
        with self._lock:
            now = time.monotonic()
            self._maybe_cleanup(now)

            if key not in self._buckets:
                water = 0.0
                last_leak = now
            else:
                water, last_leak = self._buckets[key]
                if last_leak > 1e8 and now < 1e8:
                    elapsed = 0.0
                    last_leak = now
                else:
                    elapsed = max(0.0, now - last_leak)
                    last_leak = max(last_leak, now)
                water = max(0.0, water - elapsed * self.leak_rate)

            if water + amount <= self.capacity:
                self._buckets[key] = (water + amount, last_leak)
                return True
            else:
                self._buckets[key] = (water, last_leak)
                return False

    def get_water_level(self, key: str) -> float:
        """Return current estimated water level for a key."""
        with self._lock:
            now = time.monotonic()
            if key not in self._buckets:
                return 0.0
            water, last_leak = self._buckets[key]
            if last_leak > 1e8 and now < 1e8:
                elapsed = 0.0
            else:
                elapsed = max(0.0, now - last_leak)
            return max(0.0, water - elapsed * self.leak_rate)

    def cleanup(self, max_idle: Optional[float] = None) -> int:
        """
        Purge idle client buckets that have not had requests for >= `max_idle` seconds.
        Returns the count of purged buckets.
        """
        effective_idle = float(max_idle) if max_idle is not None else self.max_idle
        with self._lock:
            now = time.monotonic()
            self._last_cleanup = now
            stale_keys = [
                k for k, (_, last_seen) in self._buckets.items()
                if (now - last_seen) >= effective_idle
            ]
            for k in stale_keys:
                del self._buckets[k]
            return len(stale_keys)

    def _maybe_cleanup(self, now: float) -> None:
        """Passive opportunistic eviction of stale buckets."""
        if (now - self._last_cleanup) >= self.cleanup_interval or len(self._buckets) >= self.max_buckets:
            self._last_cleanup = now
            stale_keys = [
                k for k, (_, last_seen) in self._buckets.items()
                if (now - last_seen) >= self.max_idle
            ]
            for k in stale_keys:
                del self._buckets[k]

            if len(self._buckets) >= self.max_buckets:
                excess = len(self._buckets) - self.max_buckets + 1
                oldest_keys = sorted(self._buckets.keys(), key=lambda k: self._buckets[k][1])[:excess]
                for k in oldest_keys:
                    del self._buckets[k]

    def reset(self, key: Optional[str] = None):
        """Reset water level for a specific key or all keys."""
        with self._lock:
            if key:
                self._buckets.pop(key, None)
            else:
                self._buckets.clear()


class MemoryCache:
    """Thread-safe in-memory cache with TTL expiration and accurate existence checking."""

    def __init__(self, default_ttl: float = 300.0):
        self.default_ttl = float(default_ttl)
        # key -> (value, expiry_timestamp)
        self._store: Dict[str, Tuple[Any, float]] = {}
        self._lock = threading.Lock()

    def get(self, key: str) -> Optional[Any]:
        """Retrieve value by key if present and unexpired; returns None if missing or expired."""
        with self._lock:
            now = time.monotonic()
            entry = self._store.get(key)
            if entry is None:
                return None
            val, exp = entry
            if now > exp:
                del self._store[key]
                return None
            return val

    def set(self, key: str, value: Any, ttl: Optional[float] = None) -> None:
        """Store key-value pair with TTL (seconds)."""
        effective_ttl = float(ttl) if ttl is not None else self.default_ttl
        with self._lock:
            now = time.monotonic()
            self._store[key] = (value, now + effective_ttl)

    def has(self, key: str) -> bool:
        """Check whether key exists and is unexpired, properly supporting None cached values."""
        with self._lock:
            now = time.monotonic()
            entry = self._store.get(key)
            if entry is None:
                return False
            _, exp = entry
            if now > exp:
                del self._store[key]
                return False
            return True

    def delete(self, key: str) -> bool:
        """Delete key from cache."""
        with self._lock:
            return self._store.pop(key, None) is not None

    def clear(self) -> None:
        """Clear all cached entries."""
        with self._lock:
            self._store.clear()

    def cleanup(self) -> int:
        """Purge all expired keys from cache. Returns count of purged keys."""
        with self._lock:
            now = time.monotonic()
            expired = [k for k, (_, exp) in self._store.items() if now > exp]
            for k in expired:
                del self._store[k]
            return len(expired)

    def size(self) -> int:
        """Return number of valid unexpired items."""
        with self._lock:
            now = time.monotonic()
            return sum(1 for _, exp in self._store.values() if now <= exp)


# Global limiter and cache instances
synthesis_limiter = TokenBucketRateLimiter(capacity=10.0, refill_rate=2.0)
cloning_limiter = TokenBucketRateLimiter(capacity=5.0, refill_rate=0.5)
streaming_limiter = LeakyBucketRateLimiter(capacity=30.0, leak_rate=5.0)
app_cache = MemoryCache(default_ttl=300.0)


def get_client_identifier(request: Request) -> str:
    """Extract client IP or forwarded identifier for rate limiting."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown_client"


async def rate_limit_synthesis(request: Request):
    """FastAPI dependency to rate limit speech synthesis calls (Token Bucket)."""
    key = get_client_identifier(request)
    if not synthesis_limiter.acquire(key, tokens=1.0):
        wait_sec = synthesis_limiter.get_wait_time(key, tokens=1.0)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Synthesis rate limit exceeded. Capacity replenishment in {wait_sec:.1f}s.",
            headers={"Retry-After": str(int(wait_sec) + 1)},
        )


async def rate_limit_cloning(request: Request):
    """FastAPI dependency to rate limit voice cloning calls (Token Bucket)."""
    key = get_client_identifier(request)
    if not cloning_limiter.acquire(key, tokens=1.0):
        wait_sec = cloning_limiter.get_wait_time(key, tokens=1.0)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Voice cloning rate limit exceeded. Capacity replenishment in {wait_sec:.1f}s.",
            headers={"Retry-After": str(int(wait_sec) + 1)},
        )


async def rate_limit_streaming(request: Request):
    """FastAPI dependency to rate limit audio stream requests (Leaky Bucket)."""
    key = get_client_identifier(request)
    if not streaming_limiter.acquire(key, amount=1.0):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Audio streaming rate limit exceeded. Connection throttled.",
            headers={"Retry-After": "2"},
        )
