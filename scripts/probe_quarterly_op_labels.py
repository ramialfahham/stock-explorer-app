#!/usr/bin/env python3
"""Report quarterly operating-profit row coverage per market (read-only)."""

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
from ingestion.yfinance.quarterly import (
    OPERATING_INCOME_FALLBACK_ROWS,
    OPERATING_EXPENSE_ROW,
    OPERATING_REVENUE_ROW,
    TOTAL_REVENUE_ROW,
    quarterly_income_statement,
    quarterly_operating_income_values,
    quarterly_row_values,
)
from ingestion.yfinance.rate_limit import call_with_retry
from ingestion.yfinance.symbols import to_yfinance_ticker


def _probe_ticker(market_code: str, exchange_suffix: str, local_ticker: str) -> dict:
    yf_symbol = to_yfinance_ticker(local_ticker, exchange_suffix)

    def _load() -> dict:
        ticker = yf.Ticker(yf_symbol)
        income = quarterly_income_statement(ticker)
        has_q = income is not None and not income.empty
        rev_ok = has_q and all(
            value is not None for value in quarterly_row_values(income, TOTAL_REVENUE_ROW)
        )
        op_ok = has_q and all(
            value is not None for value in quarterly_operating_income_values(income)
        )
        bank_ok = has_q and all(
            value is not None
            for value in quarterly_row_values(income, OPERATING_REVENUE_ROW)
        ) and all(
            value is not None
            for value in quarterly_row_values(income, OPERATING_EXPENSE_ROW)
        )
        labels = []
        if has_q:
            labels = [
                str(label)
                for label in income.index
                if any(token in str(label).lower() for token in ("operat", "ebit"))
            ]
        return {
            "market_code": market_code,
            "ticker": local_ticker,
            "has_quarterly": has_q,
            "four_q_revenue": rev_ok,
            "four_q_op_income": op_ok,
            "four_q_bank_derived": bank_ok and not op_ok,
            "four_q_op_any": op_ok or (bank_ok and rev_ok),
            "op_like_labels": labels[:6],
        }

    try:
        return call_with_retry(_load)
    except Exception as exc:  # noqa: BLE001
        return {
            "market_code": market_code,
            "ticker": local_ticker,
            "error": str(exc),
        }


def _summarize(market_code: str, rows: list[dict]) -> None:
    ok = [row for row in rows if "error" not in row]
    print(f"\n=== {market_code} (sample n={len(rows)}) ===")
    if not ok:
        print("  no successful probes")
        return
    for key, label in (
        ("has_quarterly", "quarterly income stmt"),
        ("four_q_revenue", "4Q Total Revenue"),
        ("four_q_op_income", "4Q Operating Income (fallback labels)"),
        ("four_q_bank_derived", "4Q op via Operating Revenue − Expense"),
        ("four_q_op_any", "4Q op profit (any path)"),
    ):
        count = sum(1 for row in ok if row.get(key))
        print(f"  {label}: {count}/{len(ok)} ({100 * count / len(ok):.0f}%)")
    print(f"  fallback row order: {', '.join(OPERATING_INCOME_FALLBACK_ROWS)}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--market", action="append", help="Market code (repeatable)")
    parser.add_argument("--sample", type=int, default=10, help="Random sample size per market")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args(argv)

    markets = load_markets()
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
