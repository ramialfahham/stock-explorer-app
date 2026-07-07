#!/usr/bin/env python3
"""Report balance-sheet row-label coverage per market (read-only).

Companion to ``probe_quarterly_op_labels.py``. yfinance canonicalises balance-sheet row
labels to a fixed key set, so a single canonical label per line should resolve across
markets — this probe confirms that by sampling live ``ticker.balance_sheet`` frames and
reporting, per market: for each field, the share of the sample where its label resolves to
a value, plus the raw labels present (for human audit). Findings feed
``docs/intl-balance-sheet-row-labels.md``.
"""

from __future__ import annotations

import argparse
import random
import sys
from pathlib import Path

import yfinance as yf

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ingestion.constituents.seeds import load_constituents
from ingestion.registry import load_markets
from ingestion.yfinance.balance_sheet import BALANCE_SHEET_FIELDS, latest_annual_value
from ingestion.yfinance.rate_limit import call_with_retry
from ingestion.yfinance.symbols import to_yfinance_ticker

# Keywords used to surface candidate balance-sheet labels for human audit.
_LABEL_KEYWORDS = (
    "equity",
    "debt",
    "current",
    "cash",
    "tangible",
    "asset",
    "liabilit",
    "goodwill",
    "intangible",
)


def _probe_ticker(market_code: str, exchange_suffix: str, local_ticker: str) -> dict:
    yf_symbol = to_yfinance_ticker(local_ticker, exchange_suffix)

    def _load() -> dict:
        ticker = yf.Ticker(yf_symbol)
        balance = getattr(ticker, "balance_sheet", None)
        has_bs = balance is not None and not balance.empty
        resolved = {
            field: (has_bs and latest_annual_value(balance, labels) is not None)
            for field, labels in BALANCE_SHEET_FIELDS.items()
        }
        labels: list[str] = []
        if has_bs:
            labels = [
                str(label)
                for label in balance.index
                if any(token in str(label).lower() for token in _LABEL_KEYWORDS)
            ]
        return {
            "market_code": market_code,
            "ticker": local_ticker,
            "has_balance_sheet": has_bs,
            "resolved": resolved,
            "bs_labels": labels[:12],
        }

    try:
        return call_with_retry(_load)
    except Exception as exc:  # noqa: BLE001
        return {"market_code": market_code, "ticker": local_ticker, "error": str(exc)}


def _summarize(market_code: str, rows: list[dict]) -> None:
    ok = [row for row in rows if "error" not in row]
    print(f"\n=== {market_code} (sample n={len(rows)}) ===")
    if not ok:
        print("  no successful probes")
        return
    has_bs = sum(1 for row in ok if row.get("has_balance_sheet"))
    print(f"  balance sheet present: {has_bs}/{len(ok)} ({100 * has_bs / len(ok):.0f}%)")
    for field in BALANCE_SHEET_FIELDS:
        count = sum(1 for row in ok if row.get("resolved", {}).get(field))
        print(f"  {field}: {count}/{len(ok)} ({100 * count / len(ok):.0f}%)")
    seen: dict[str, int] = {}
    for row in ok:
        for label in row.get("bs_labels", []):
            seen[label] = seen.get(label, 0) + 1
    if seen:
        top = sorted(seen.items(), key=lambda kv: kv[1], reverse=True)[:20]
        print("  candidate labels seen (label: count):")
        for label, count in top:
            print(f"    {label}: {count}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--market", action="append", help="Market code (repeatable)")
    parser.add_argument("--sample", type=int, default=10, help="Random sample size per market")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args(argv)

    markets = load_markets(active_only=True)
    if args.market:
        wanted = set(args.market)
        markets = [market for market in markets if market.market_code in wanted]

    random.seed(args.seed)
    for market in markets:
        constituents = load_constituents(market.market_code)
        tickers = constituents["ticker"].tolist()
        sample = tickers if len(tickers) <= args.sample else random.sample(tickers, args.sample)
        rows = [
            _probe_ticker(market.market_code, market.exchange_suffix, ticker)
            for ticker in sample
        ]
        _summarize(market.market_code, rows)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
