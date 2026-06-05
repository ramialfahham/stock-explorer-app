#!/usr/bin/env python3
"""Sample yfinance field coverage per market (read-only; see docs/data_contract.md)."""

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
from ingestion.yfinance.ingest import INFO_FIELDS
from ingestion.yfinance.rate_limit import call_with_retry, is_rate_limited
from ingestion.yfinance.symbols import to_yfinance_download_ticker, to_yfinance_ticker

INCOME_ROW = "Total Revenue"
CASHFLOW_ROW = "Free Cash Flow"

INFO_KEYS = tuple(INFO_FIELDS.values())
FIELD_LABELS = {
    "forwardPE": "forward_pe (info)",
    "operatingMargins": "ebit_margin (info)",
    "revenueGrowth": "revenue_growth (info)",
    "netDebt": "net_debt (info)",
    "totalDebtCash": "total_debt & total_cash (info)",
    "ebitda": "ebitda (info)",
    "stmt_total_revenue": "total_revenue (stmt)",
    "stmt_free_cash_flow": "fcf (stmt)",
}


def _has_statement_row(ticker: yf.Ticker, row_label: str) -> bool:
    for frame in (ticker.income_stmt, ticker.financials, ticker.cashflow):
        if frame is not None and not frame.empty and row_label in frame.index:
            return True
    return False


def _audit_ticker(market_code: str, exchange_suffix: str, local_ticker: str) -> dict:
    yf_symbol = to_yfinance_ticker(local_ticker, exchange_suffix)
    download_symbol = to_yfinance_download_ticker(local_ticker, exchange_suffix)

    def _probe() -> dict:
        t = yf.Ticker(yf_symbol)
        info = t.info or {}
        hits = {
            "forwardPE": info.get("forwardPE") is not None,
            "operatingMargins": info.get("operatingMargins") is not None,
            "revenueGrowth": info.get("revenueGrowth") is not None,
            "netDebt": info.get("netDebt") is not None,
            "totalDebtCash": info.get("totalDebt") is not None and info.get("totalCash") is not None,
            "ebitda": info.get("ebitda") is not None,
            "stmt_total_revenue": _has_statement_row(t, INCOME_ROW),
            "stmt_free_cash_flow": _has_statement_row(t, CASHFLOW_ROW),
        }
        row = {
            "market_code": market_code,
            "ticker": local_ticker,
            "yf_symbol": yf_symbol,
            "info_keys": len(info),
        }
        for key, ok in hits.items():
            row[key] = ok

        row["card_eligible"] = (
            hits["forwardPE"]
            and hits["operatingMargins"]
            and hits["revenueGrowth"]
            and hits["ebitda"]
            and (hits["netDebt"] or hits["totalDebtCash"])
            and hits["stmt_total_revenue"]
            and hits["stmt_free_cash_flow"]
        )

        hist = t.history(period="5d")
        row["history_rows"] = len(hist)
        dl = yf.download(
            download_symbol,
            period="5d",
            progress=False,
            auto_adjust=False,
        )
        row["download_rows"] = len(dl)
        return row

    try:
        return call_with_retry(_probe)
    except Exception as exc:  # noqa: BLE001
        return {
            "market_code": market_code,
            "ticker": local_ticker,
            "yf_symbol": yf_symbol,
            "error": str(exc),
            "rate_limited": is_rate_limited(exc),
        }


def _print_summary(market_code: str, results: list[dict]) -> None:
    ok = [r for r in results if "error" not in r]
    failed = [r for r in results if "error" in r]
    eligible = sum(1 for r in ok if r.get("card_eligible"))

    print(f"\n=== {market_code} (n={len(results)}) ===")
    if failed:
        print(f"  errors: {len(failed)} (rate_limited={sum(1 for r in failed if r.get('rate_limited'))})")

    for key, label in FIELD_LABELS.items():
        count = sum(1 for r in ok if r.get(key))
        pct = 100 * count / len(ok) if ok else 0
        print(f"  {label}: {count}/{len(ok)} ({pct:.0f}%)")

    if ok:
        hist_ok = sum(1 for r in ok if r.get("history_rows", 0) > 0)
        dl_ok = sum(1 for r in ok if r.get("download_rows", 0) > 0)
        print(f"  history(5d) ok: {hist_ok}/{len(ok)}")
        print(f"  download(5d) ok: {dl_ok}/{len(ok)}")

    print(f"  estimated card_eligible: {eligible}/{len(ok)} ({100*eligible/len(ok):.0f}%)" if ok else "  estimated card_eligible: n/a")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Audit yfinance coverage for card metrics")
    parser.add_argument("--market", action="append", dest="markets", help="market_code (repeatable)")
    parser.add_argument("--sample-size", type=int, default=10)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args(argv)

    markets = load_markets(active_only=True)
    if args.markets:
        selected = set(args.markets)
        markets = [m for m in markets if m.market_code in selected]

    if not markets:
        print("No markets to audit.", file=sys.stderr)
        return 1

    rng = random.Random(args.seed)

    for market in markets:
        constituents = load_constituents(market.market_code)
        tickers = constituents["ticker"].tolist()
        sample = tickers if len(tickers) <= args.sample_size else rng.sample(
            tickers, args.sample_size
        )

        print(f"Auditing {market.market_code} ({len(sample)} tickers)...")
        results = []
        for ticker in sample:
            results.append(
                _audit_ticker(market.market_code, market.exchange_suffix, ticker)
            )
        _print_summary(market.market_code, results)

    print("\naudit_yfinance_coverage: done (informational exit 0)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
