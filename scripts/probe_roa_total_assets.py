#!/usr/bin/env python3
"""Probe ROA / Total Assets / Net Income Common coverage for the metric enrichment (read-only).

Slice 3a needs two raw statement lines that are not yet ingested:
  - balance-sheet "Total Assets"                 -> stmt_total_assets
    (for ROA = net income / total assets — a leverage-neutral returns metric for financials)
  - income "Net Income Common Stockholders"      -> stmt_net_income_common
    (for a correctly-attributed ROE = common income / common equity, fixing the #141 mismatch
    where consolidated net income was divided by parent-only equity)

This probe samples a few live tickers (defaults: JPM, BAC, HSBA.L financials + MSFT control) and
reports, per ticker: the yfinance ``info.returnOnAssets`` / ``returnOnEquity`` scalars; the
balance-sheet Total Assets + Stockholders Equity; the income Net Income + Net Income Common
Stockholders; and the ROA/ROE computed from those statement lines, cross-checked against the info
scalars. It also dumps the raw income/balance labels so the exact canonical strings are confirmed
before wiring. Prints only — no writes, no parquet, deterministic ordering.
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import yfinance as yf

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ingestion.yfinance.balance_sheet import latest_annual_value
from ingestion.yfinance.rate_limit import call_with_retry

DEFAULT_TICKERS = ("JPM", "BAC", "HSBA.L", "MSFT")

# Candidate labels (ordered fallback) for the lines this probe inspects. yfinance
# canonicalises statement row labels, so a single string should resolve; equity has a
# genuine alternate (mirrors ingestion/yfinance/balance_sheet.py).
TOTAL_ASSETS_LABELS = ("Total Assets",)
STOCKHOLDERS_EQUITY_LABELS = ("Stockholders Equity", "Common Stock Equity")
NET_INCOME_LABELS = ("Net Income",)
NET_INCOME_COMMON_LABELS = ("Net Income Common Stockholders",)


def _fmt(value: float | None) -> str:
    if value is None:
        return "—"
    if isinstance(value, float):
        return f"{value:,.0f}" if abs(value) >= 1000 else f"{value:,.4f}"
    return str(value)


def _pct(value: float | None) -> str:
    return "—" if value is None else f"{value * 100:.2f}%"


def _ratio(num: float | None, den: float | None) -> float | None:
    if num is None or den in (None, 0):
        return None
    return num / den


def _income_frame(ticker: object):
    income = ticker.income_stmt
    if income is None or income.empty:
        income = ticker.financials
    return income


def _matching_labels(frame, needle: str) -> list[str]:
    if frame is None or getattr(frame, "empty", True):
        return []
    return [str(lbl) for lbl in frame.index if needle in str(lbl).lower()]


def _probe(symbol: str) -> dict:
    def _load() -> dict:
        ticker = yf.Ticker(symbol)
        info = ticker.info or {}
        balance = getattr(ticker, "balance_sheet", None)
        income = _income_frame(ticker)

        total_assets = latest_annual_value(balance, TOTAL_ASSETS_LABELS)
        equity = latest_annual_value(balance, STOCKHOLDERS_EQUITY_LABELS)
        net_income = latest_annual_value(income, NET_INCOME_LABELS)
        net_income_common = latest_annual_value(income, NET_INCOME_COMMON_LABELS)

        return {
            "symbol": symbol,
            "roa_scalar": info.get("returnOnAssets"),
            "roe_scalar": info.get("returnOnEquity"),
            "total_assets": total_assets,
            "equity": equity,
            "net_income": net_income,
            "net_income_common": net_income_common,
            "computed_roa": _ratio(net_income, total_assets),
            "computed_roe": _ratio(net_income_common, equity),
            "income_ni_labels": _matching_labels(income, "net income"),
            "balance_asset_labels": _matching_labels(balance, "total asset"),
        }

    try:
        return call_with_retry(_load)
    except Exception as exc:  # noqa: BLE001
        return {"symbol": symbol, "error": str(exc)}


def _report(row: dict) -> None:
    print(f"\n=== {row['symbol']} ===")
    if "error" in row:
        print(f"  ERROR: {row['error']}")
        return

    ni = row["net_income"]
    nic = row["net_income_common"]
    print(f"  info.returnOnAssets        : {_pct(row['roa_scalar'])}   (raw {row['roa_scalar']})")
    print(f"  info.returnOnEquity        : {_pct(row['roe_scalar'])}   (raw {row['roe_scalar']})")
    print(f"  BS Total Assets            : {_fmt(row['total_assets'])}")
    print(f"  BS Stockholders Equity     : {_fmt(row['equity'])}")
    print(f"  IS Net Income (total)      : {_fmt(ni)}")
    print(f"  IS Net Income Common Stock : {_fmt(nic)}")
    print(f"  computed ROA (NI/TA)       : {_pct(row['computed_roa'])}   vs scalar {_pct(row['roa_scalar'])}")
    print(f"  computed ROE (NIC/SE)      : {_pct(row['computed_roe'])}   vs scalar {_pct(row['roe_scalar'])}")
    if ni and nic is not None:
        gap = (ni - nic) / ni if ni else None
        print(f"  minority-interest share (NI-NIC)/NI : {_pct(gap)}")
    print(f"  income labels ~ 'net income'   : {row['income_ni_labels']}")
    print(f"  balance labels ~ 'total asset' : {row['balance_asset_labels']}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ticker", action="append", help="yfinance symbol (repeatable)")
    parser.add_argument("--delay", type=float, default=1.0, help="Seconds between tickers")
    args = parser.parse_args(argv)

    tickers = args.ticker or list(DEFAULT_TICKERS)
    for index, symbol in enumerate(tickers):
        _report(_probe(symbol))
        if args.delay and index < len(tickers) - 1:
            time.sleep(args.delay)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
