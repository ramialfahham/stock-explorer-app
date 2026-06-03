"""Retry helpers for Yahoo rate limits during ingestion."""

from __future__ import annotations

import time
from collections.abc import Callable
from typing import TypeVar

T = TypeVar("T")

try:
    from yfinance.exceptions import YFRateLimitError
except ImportError:  # pragma: no cover - older yfinance
    YFRateLimitError = None  # type: ignore[misc, assignment]


def is_rate_limited(exc: BaseException) -> bool:
    if YFRateLimitError is not None and isinstance(exc, YFRateLimitError):
        return True
    message = str(exc).lower()
    return "too many requests" in message or "rate limit" in message or "429" in message


def call_with_retry(
    fn: Callable[[], T],
    *,
    max_attempts: int = 4,
    base_delay_seconds: float = 2.0,
) -> T:
    last_exc: BaseException | None = None
    for attempt in range(max_attempts):
        try:
            return fn()
        except BaseException as exc:
            last_exc = exc
            if not is_rate_limited(exc) or attempt == max_attempts - 1:
                raise
            delay = base_delay_seconds * (2**attempt)
            time.sleep(delay)
    assert last_exc is not None
    raise last_exc
