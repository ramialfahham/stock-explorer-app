"""Detect duplicate browse widget keys from multi-snapshot card loads."""

from __future__ import annotations

import json
import time
from pathlib import Path

from explore_filters import ALL_SECTORS, dedupe_to_latest_snapshot, filter_pool

LOG_PATH = Path(__file__).resolve().parents[1] / "debug-669620.log"
SESSION_ID = "669620"


def _log(hypothesis_id: str, message: str, data: dict) -> None:
    # #region agent log
    payload = {
        "sessionId": SESSION_ID,
        "runId": "browse-dup-post-fix",
        "hypothesisId": hypothesis_id,
        "location": "debug_browse_duplicate_keys.py",
        "message": message,
        "data": data,
        "timestamp": int(time.time() * 1000),
    }
    with LOG_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload) + "\n")
    # #endregion


def _card_key(card: dict) -> tuple[str, str]:
    return (card["market_code"], card["ticker"])


def main() -> int:
    # Simulates Supabase returning two snapshot rows for the same ticker (H1).
    cards = [
        {
            "market_code": "us_sp500",
            "ticker": "ALLE",
            "company_name": "Allegion",
            "sector": "Industrials",
            "is_card_eligible": True,
            "snapshot_date": "2026-06-01",
        },
        {
            "market_code": "us_sp500",
            "ticker": "ALLE",
            "company_name": "Allegion",
            "sector": "Industrials",
            "is_card_eligible": True,
            "snapshot_date": "2026-06-08",
        },
        {
            "market_code": "us_sp500",
            "ticker": "AAPL",
            "company_name": "Apple",
            "sector": "Technology",
            "is_card_eligible": True,
            "snapshot_date": "2026-06-08",
        },
    ]

    pool = filter_pool(
        dedupe_to_latest_snapshot(cards),
        [],
        market_code="us_sp500",
        sector=ALL_SECTORS,
        surprise_me=False,
    )
    widget_keys = [f"browse_{key[0]}_{key[1]}" for key in (_card_key(c) for c in pool)]
    dupes = sorted({k for k in widget_keys if widget_keys.count(k) > 1})

    _log(
        "H1",
        "browse widget keys from multi-snapshot pool",
        {
            "pool_size": len(pool),
            "unique_card_keys": len(set(_card_key(c) for c in pool)),
            "duplicate_widget_keys": dupes,
            "would_crash_streamlit": bool(dupes),
        },
    )

    return 1 if dupes else 0


if __name__ == "__main__":
    raise SystemExit(main())
