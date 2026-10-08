from functools import lru_cache
from typing import Annotated

from fastapi import Depends, HTTPException, Response, status

from personal_document_intelligence_api.api.dependencies.auth import (
    get_current_owner_id,
)
from personal_document_intelligence_api.core.config import Settings, get_settings
from personal_document_intelligence_api.core.rate_limit import InMemoryRateLimiter


@lru_cache
def get_rate_limiter() -> InMemoryRateLimiter:
    return InMemoryRateLimiter()


def enforce_expensive_rate_limit(
    response: Response,
    owner_id: Annotated[str, Depends(get_current_owner_id)],
    settings: Annotated[Settings, Depends(get_settings)],
    limiter: Annotated[InMemoryRateLimiter, Depends(get_rate_limiter)],
) -> None:
    result = limiter.consume(
        key=f"expensive:{owner_id}",
        limit=settings.expensive_rate_limit_requests,
        window_seconds=settings.expensive_rate_limit_window_seconds,
    )
    response.headers["X-RateLimit-Limit"] = str(settings.expensive_rate_limit_requests)
    response.headers["X-RateLimit-Remaining"] = str(result.remaining)
    if not result.allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Hourly AI request limit reached",
            headers={"Retry-After": str(result.retry_after_seconds)},
        )
