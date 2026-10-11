"""Retry rules for Yahoo rate limits: only a rate-limit error is retried, with doubling waits,
and it is raised once the attempts are used up. `time.sleep` is patched, so no real waiting."""

from __future__ import annotations

import pytest

from ingestion.yfinance import rate_limit


class FakeRateLimitError(Exception):
    pass


@pytest.fixture
def sleeps(monkeypatch: pytest.MonkeyPatch) -> list[float]:
    recorded: list[float] = []
    monkeypatch.setattr(rate_limit.time, "sleep", recorded.append)
    monkeypatch.setattr(rate_limit, "YFRateLimitError", FakeRateLimitError)
    return recorded


def _failing(error: Exception, calls: list[int]):
    def fn():
        calls.append(1)
        raise error

    return fn


@pytest.mark.parametrize(
    "error",
    [
        FakeRateLimitError("anything"),
        RuntimeError("HTTP Error 429"),
        RuntimeError("Too Many Requests"),
        RuntimeError("rate limit hit"),
    ],
)
def test_rate_limit_errors_are_recognised(error: Exception, sleeps: list[float]) -> None:
    assert rate_limit.is_rate_limited(error)


def test_other_errors_are_not_rate_limits(sleeps: list[float]) -> None:
    assert not rate_limit.is_rate_limited(ValueError("bad ticker"))


def test_a_non_rate_limit_error_is_raised_after_one_call(sleeps: list[float]) -> None:
    calls: list[int] = []
    with pytest.raises(ValueError):
        rate_limit.call_with_retry(_failing(ValueError("bad ticker"), calls))
    assert len(calls) == 1
    assert sleeps == []


def test_a_rate_limit_error_is_retried_then_raised_after_max_attempts(sleeps: list[float]) -> None:
    calls: list[int] = []
    with pytest.raises(RuntimeError, match="429"):
        rate_limit.call_with_retry(
            _failing(RuntimeError("429"), calls), max_attempts=3, base_delay_seconds=2.0
        )
    assert len(calls) == 3
    assert sleeps == [2.0, 4.0]


def test_a_success_after_one_429_returns_the_value(sleeps: list[float]) -> None:
    outcomes = iter([RuntimeError("Too Many Requests"), "payload"])

    def fn():
        outcome = next(outcomes)
        if isinstance(outcome, Exception):
            raise outcome
        return outcome

    assert rate_limit.call_with_retry(fn) == "payload"
    assert sleeps == [2.0]
