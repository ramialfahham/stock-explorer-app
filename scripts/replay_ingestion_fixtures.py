"""Replay the recorded real-shaped payloads through the real ingestion code, offline.

Runs `ingestion.yfinance.ingest.ingest_market` for every active market with `yf` swapped for
the recordings in `tests/fixtures/real/` and the seed narrowed to the recorded tickers, so the
raw parquet it writes is what production would write for those companies. Price dates are
moved onto the business days ending on or before `--today`, so the raw files have a live
run's shape; only the staging model `stg_yf__daily_prices` reads them, no card mart does. Any
yfinance call the recordings do not hold raises instead of guessing.
"""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from datetime import date, datetime, timezone
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pandas as pd

from ingestion.constituents import seeds
from ingestion.registry import load_markets
from ingestion.yfinance import ingest

FIXTURE_DIR = ROOT / "tests" / "fixtures" / "real"
TICKER_FRAMES = (
    "income_stmt",
    "financials",
    "cashflow",
    "quarterly_income_stmt",
    "quarterly_financials",
    "balance_sheet",
)


def frame_from_json(obj: dict | None) -> pd.DataFrame | None:
    if obj is None:
        return None
    frame = pd.DataFrame(
        obj["data"], index=obj["index"], columns=pd.to_datetime(obj["columns"]), dtype=float
    )
    frame.attrs.update(obj.get("attrs") or {})
    return frame


class FixtureTicker:
    """Answers exactly the `yf.Ticker` attributes that were recorded, and nothing else."""

    def __init__(self, payload: dict):
        self.info = dict(payload["info"])
        for name in TICKER_FRAMES:
            setattr(self, name, frame_from_json(payload[name]))

    def __getattr__(self, name: str):
        raise AttributeError(f"yf.Ticker.{name} was not recorded; re-record the fixtures")


class FixtureYfinance:
    """Stands in for the `yfinance` module inside `ingest.py`."""

    def __init__(self, market_code: str, today: date):
        base = FIXTURE_DIR / "yfinance" / market_code
        self._tickers = {
            p.stem: json.loads(p.read_text(encoding="utf-8")) for p in base.glob("*.json")
        }
        self._prices = pd.read_parquet(base / "prices.parquet")
        self._today = today

    def Ticker(self, symbol: str) -> FixtureTicker:  # noqa: N802 -- mirrors yfinance's API
        if symbol not in self._tickers:
            raise KeyError(f"no recording for yf.Ticker({symbol!r})")
        return FixtureTicker(self._tickers[symbol])

    def download(self, tickers: list[str], **_kwargs) -> pd.DataFrame:
        recorded = set(self._prices["symbol"].unique())
        unknown = [t for t in tickers if t not in recorded]
        if unknown:
            raise KeyError(f"no recorded prices for {unknown}")
        parts = {}
        for symbol in tickers:
            part = self._prices[self._prices["symbol"] == symbol].drop(columns="symbol")
            part = part.sort_values("Date").set_index("Date")
            part.index = pd.bdate_range(end=pd.Timestamp(self._today), periods=len(part), name="Date")
            parts[symbol] = part
        return pd.concat(parts, axis=1, names=["Ticker", "Price"])


def _frozen_datetime(today: date) -> type[datetime]:
    """`datetime` whose `now()` is noon UTC on `today`: ingest stamps snapshot_date with it."""

    class _Frozen(datetime):
        @classmethod
        def now(cls, tz=None):
            return datetime(today.year, today.month, today.day, 12, tzinfo=timezone.utc)

    return _Frozen


def _narrowed_seed(market_code: str, keep: set[str], work: Path) -> Path:
    """The committed seed's own rows for the recorded tickers, so overrides still apply."""
    frame = seeds.load_constituents(market_code)
    raw = pd.read_csv(seeds.seed_path(market_code), dtype=str, na_filter=False)
    raw = raw[frame["ticker"].isin(keep).to_numpy()]
    path = work / market_code / "constituents.csv"
    path.parent.mkdir(parents=True, exist_ok=True)
    raw.to_csv(path, index=False)
    return path


def replay(out_dir: Path, today: date) -> dict[str, dict]:
    manifest = json.loads((FIXTURE_DIR / "manifest.json").read_text(encoding="utf-8"))
    results: dict[str, dict] = {}
    with tempfile.TemporaryDirectory() as tmp:
        work = Path(tmp)
        for market in load_markets(active_only=True):
            code = market.market_code
            entry = manifest["markets"].get(code)
            if entry is None:
                raise SystemExit(f"{code} is active but has no recordings; run the recorder")
            seed = _narrowed_seed(code, set(entry["tickers"]), work)
            with mock.patch.object(ingest, "yf", FixtureYfinance(code, today)), \
                    mock.patch.object(ingest, "raw_dir", lambda c: out_dir / c), \
                    mock.patch.object(seeds, "seed_path", lambda c, s=seed: s), \
                    mock.patch.object(ingest, "datetime", _frozen_datetime(today)):
                results[code] = ingest.ingest_market(market, force=True)
    return results


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out-dir", type=Path, required=True, help="raw parquet root to write")
    parser.add_argument("--today", type=date.fromisoformat, default=date.today(),
                        help="the run date the replay pretends it is (default: today)")
    args = parser.parse_args(argv)
    for code, stats in replay(args.out_dir, args.today).items():
        print(f"{code}: " + " ".join(f"{k}={v}" for k, v in stats.items()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
