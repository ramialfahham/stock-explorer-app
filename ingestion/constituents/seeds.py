"""Read and write constituent seed CSV files."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from ingestion.paths import seed_path

SEED_COLUMNS = ("market_code", "ticker", "company_name", "refreshed_at", "source")


def load_constituents(market_code: str) -> pd.DataFrame:
    path = seed_path(market_code)
    if not path.exists():
        raise FileNotFoundError(
            f"Missing seed file for {market_code}: {path}. "
            "Run scripts/refresh_constituents.py or scripts/import_constituents.py."
        )

    frame = pd.read_csv(path)
    missing = [col for col in SEED_COLUMNS if col not in frame.columns]
    if missing:
        raise ValueError(f"{path} missing columns: {missing}")

    return frame[list(SEED_COLUMNS)].copy()


def write_constituents(
    market_code: str,
    tickers: pd.Series,
    company_names: pd.Series,
    *,
    source: str,
    refreshed_at: datetime | None = None,
) -> Path:
    refreshed = refreshed_at or datetime.now(timezone.utc)
    frame = pd.DataFrame(
        {
            "market_code": market_code,
            "ticker": tickers.astype(str).str.strip(),
            "company_name": company_names.astype(str).str.strip(),
            "refreshed_at": refreshed.isoformat(),
            "source": source,
        }
    )
    frame = frame.dropna(subset=["ticker"])
    frame = frame[frame["ticker"] != ""]
    frame = frame.drop_duplicates(subset=["ticker"], keep="first")

    path = seed_path(market_code)
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, index=False)
    return path
