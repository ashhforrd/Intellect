from dataclasses import dataclass
from threading import Lock
from time import monotonic


@dataclass(frozen=True, slots=True)
class RateLimitResult:
    allowed: bool
    remaining: int
    retry_after_seconds: int


@dataclass(slots=True)
class RateLimitBucket:
    count: int
    reset_at: float


class InMemoryRateLimiter:
    def __init__(self) -> None:
        self.buckets: dict[str, RateLimitBucket] = {}
        self.lock = Lock()

    def consume(self, key: str, limit: int, window_seconds: int) -> RateLimitResult:
        now = monotonic()
        with self.lock:
            bucket = self.buckets.get(key)
            if bucket is None or now >= bucket.reset_at:
                bucket = RateLimitBucket(count=0, reset_at=now + window_seconds)
                self.buckets[key] = bucket

            retry_after = max(1, int(bucket.reset_at - now))
            if bucket.count >= limit:
                return RateLimitResult(False, 0, retry_after)

            bucket.count += 1
            return RateLimitResult(True, limit - bucket.count, retry_after)
