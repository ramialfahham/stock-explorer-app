#!/usr/bin/env python3
"""Compare mart_stock_cards metrics to live yfinance (see docs/metric_audit.md)."""

from __future__ import annotations

import argparse
import csv
import json
import random
import sys
from datetime import date, datetime, timezone
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from ingestion.registry import load_markets
from ingestion.yfinance.ingest import _fetch_fundamentals_row
from ingestion.yfinance.rate_limit import is_rate_limited
from metric_formulas import (
    compute_card_metrics_from_raw,
    pct_drift,
    reference_fcf_margin_from_info,
    reference_operating_margin_info,
    reference_operating_margin_ttm,
)

DEFAULT_ALWAYS = ("ABNB", "NVDA", "AAPL", "ALB")
MART_COLUMNS = (
    "market_code",
    "ticker",
    "company_name",
    "sector",
    "snapshot_date",
    "business_summary",
    "forward_pe",
    "ebit_margin_pct",
    "revenue_growth_yoy_pct",
    "net_debt_to_ebitda",
    "fcf_margin_pct",
    "is_card_eligible",
)
METRIC_KEYS = (
    "forward_pe",
    "ebit_margin_pct",
    "revenue_growth_yoy_pct",
    "net_debt_to_ebitda",
    "fcf_margin_pct",
)


def _parse_date(raw: object) -> date | None:
    if raw is None:
        return None
    if isinstance(raw, date):
        return raw
    try:
        return date.fromisoformat(str(raw)[:10])
    except ValueError:
        return None


def _snapshot_age_days(snapshot_date: object) -> int | None:
    parsed = _parse_date(snapshot_date)
    if parsed is None:
        return None
    return (datetime.now(timezone.utc).date() - parsed).days


def _load_mart_from_duckdb(db_path: Path) -> list[dict]:
    conn = duckdb.connect(str(db_path), read_only=True)
    try:
        cols = ", ".join(MART_COLUMNS)
        rows = conn.execute(
            f"select {cols} from marts.mart_stock_cards where is_card_eligible = true"
        ).fetchall()
        columns = [desc[0] for desc in conn.description]
    finally:
        conn.close()
    return [dict(zip(columns, row, strict=True)) for row in rows]


def _load_mart_from_supabase() -> list[dict]:
    from supabase import create_client

    import os

    from dotenv import load_dotenv

    load_dotenv()
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_ANON_KEY")
    if not url or not key:
        raise RuntimeError("Missing SUPABASE_URL or Supabase key in environment")

    client = create_client(url, key)
    response = (
        client.table("mart_stock_cards")
        .select(",".join(MART_COLUMNS))
        .eq("is_card_eligible", True)
        .execute()
    )
    return response.data or []


def _market_lookup() -> dict[str, object]:
    return {m.market_code: m for m in load_markets(active_only=True)}


def _pick_sample(
    mart_rows: list[dict],
    *,
    sample_size: int,
    always_tickers: tuple[str, ...],
    seed: int,
) -> list[dict]:
    by_key = {(r["market_code"], r["ticker"]): r for r in mart_rows}
    chosen: list[dict] = []
    seen: set[tuple[str, str]] = set()

    for ticker in always_tickers:
        for row in mart_rows:
            if row["ticker"] == ticker and (row["market_code"], row["ticker"]) not in seen:
                chosen.append(row)
                seen.add((row["market_code"], row["ticker"]))
                break

    pool = [r for r in mart_rows if (r["market_code"], r["ticker"]) not in seen]
    rng = random.Random(seed)
    rng.shuffle(pool)
    for row in pool:
        if len(chosen) >= sample_size:
            break
        key = (row["market_code"], row["ticker"])
        if key in seen:
            continue
        chosen.append(row)
        seen.add(key)
    return chosen


def _fetch_live_row(market_code: str, ticker: str, markets: dict) -> dict | None:
    market = markets.get(market_code)
    if market is None:
        return None
    from ingestion.yfinance.symbols import to_yfinance_ticker

    yf_symbol = to_yfinance_ticker(ticker, market.exchange_suffix)
    try:
        return _fetch_fundamentals_row(
            market,
            ticker,
            yf_symbol,
            datetime.now(timezone.utc).date(),
        )
    except Exception as exc:  # noqa: BLE001
        label = "rate-limited" if is_rate_limited(exc) else "error"
        print(f"  warning: live fetch {label} for {market_code}/{ticker}: {exc}", file=sys.stderr)
        return None


def _audit_row(mart: dict, live_raw: dict | None) -> dict:
    out: dict = {
        "market_code": mart["market_code"],
        "ticker": mart["ticker"],
        "company_name": mart.get("company_name"),
        "sector": mart.get("sector"),
        "snapshot_date": str(mart.get("snapshot_date") or ""),
        "snapshot_age_days": _snapshot_age_days(mart.get("snapshot_date")),
        "business_summary_present": bool(str(mart.get("business_summary") or "").strip()),
    }

    for metric in METRIC_KEYS:
        out[f"mart_{metric}"] = mart.get(metric)

    if live_raw is None:
        out["live_fetch_ok"] = False
        return out

    live_metrics = compute_card_metrics_from_raw(live_raw)
    out["live_fetch_ok"] = True
    for metric in METRIC_KEYS:
        out[f"live_{metric}"] = live_metrics.get(metric)
        out[f"drift_pct_{metric}"] = pct_drift(mart.get(metric), live_metrics.get(metric))

    import yfinance as yf
    from ingestion.yfinance.symbols import to_yfinance_ticker

    market = _market_lookup().get(mart["market_code"])
    if market is not None:
        yf_symbol = to_yfinance_ticker(mart["ticker"], market.exchange_suffix)
        yf_ticker = yf.Ticker(yf_symbol)
        info = yf_ticker.info or {}
        out["reference_fcf_margin_info"] = reference_fcf_margin_from_info(info)
        out["reference_forward_pe"] = info.get("forwardPE")
        out["reference_operating_margin_info"] = reference_operating_margin_info(info)
        out["reference_operating_margin_ttm"] = reference_operating_margin_ttm(
            {"_yf_ticker": yf_ticker}
        )
        out["drift_pct_ebit_margin_vs_info"] = pct_drift(
            mart.get("ebit_margin_pct"),
            out["reference_operating_margin_info"],
        )
        out["drift_pct_ebit_margin_vs_ttm"] = pct_drift(
            mart.get("ebit_margin_pct"),
            out["reference_operating_margin_ttm"],
        )

    return out


def _summarize(rows: list[dict]) -> dict:
    summary: dict[str, object] = {
        "rows": len(rows),
        "live_fetch_ok": sum(1 for r in rows if r.get("live_fetch_ok")),
        "business_summary_fill_rate": round(
            sum(1 for r in rows if r.get("business_summary_present")) / max(len(rows), 1),
            3,
        ),
    }
    for metric in METRIC_KEYS:
        drifts = [r[f"drift_pct_{metric}"] for r in rows if r.get(f"drift_pct_{metric}") is not None]
        if drifts:
            summary[f"median_drift_pct_{metric}"] = round(sorted(drifts)[len(drifts) // 2], 2)
            summary[f"max_drift_pct_{metric}"] = round(max(drifts), 2)
    return summary


def _write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        return
    fieldnames = list(rows[0].keys())
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _check_failures(rows: list[dict], *, max_drift_pct: float, pilot_tickers: set[str]) -> list[str]:
    failures: list[str] = []
    for row in rows:
        if row["ticker"] not in pilot_tickers:
            continue
        for metric in METRIC_KEYS:
            drift = row.get(f"drift_pct_{metric}")
            if drift is not None and drift > max_drift_pct:
                failures.append(
                    f"{row['ticker']} {metric}: drift {drift:.1f}% "
                    f"(mart={row.get(f'mart_{metric}')} live={row.get(f'live_{metric}')})"
                )
    return failures


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Audit mart metrics vs live yfinance")
    parser.add_argument(
        "--source",
        choices=("duckdb", "supabase"),
        default="duckdb",
    )
    parser.add_argument(
        "--duckdb-path",
        default=str(ROOT / "storage" / "stock_data.db"),
    )
    parser.add_argument("--sample-size", type=int, default=30)
    parser.add_argument(
        "--always",
        default=",".join(DEFAULT_ALWAYS),
        help="Comma-separated tickers always included in sample",
    )
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument(
        "--offline",
        action="store_true",
        help="Skip live yfinance fetches (CI mode)",
    )
    parser.add_argument(
        "--output-dir",
        default=str(ROOT / "storage" / "audit"),
    )
    parser.add_argument(
        "--fail-on-drift",
        action="store_true",
        help="Exit 1 when pilot tickers exceed --max-drift-pct",
    )
    parser.add_argument("--max-drift-pct", type=float, default=25.0)
    parser.add_argument(
        "--pilot-tickers",
        default=",".join(DEFAULT_ALWAYS),
        help="Tickers subject to --fail-on-drift",
    )
    args = parser.parse_args(argv)

    if args.source == "duckdb":
        db_path = Path(args.duckdb_path)
        if not db_path.exists():
            print(f"DuckDB not found: {db_path}", file=sys.stderr)
            return 1
        mart_rows = _load_mart_from_duckdb(db_path)
    else:
        mart_rows = _load_mart_from_supabase()

    always = tuple(t.strip().upper() for t in args.always.split(",") if t.strip())
    sample = _pick_sample(
        mart_rows,
        sample_size=args.sample_size,
        always_tickers=always,
        seed=args.seed,
    )
    print(f"Auditing {len(sample)} tickers from {len(mart_rows)} eligible mart rows")

    markets = _market_lookup()
    audit_rows: list[dict] = []
    for mart in sample:
        live_raw = None if args.offline else _fetch_live_row(mart["market_code"], mart["ticker"], markets)
        audit_rows.append(_audit_row(mart, live_raw))

    summary = _summarize(audit_rows)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    csv_path = output_dir / f"metric_audit_{stamp}.csv"
    json_path = output_dir / f"metric_audit_{stamp}.json"
    _write_csv(csv_path, audit_rows)
    json_path.write_text(
        json.dumps({"summary": summary, "rows": audit_rows}, indent=2),
        encoding="utf-8",
    )

    print(f"Wrote {csv_path}")
    print(f"Wrote {json_path}")
    print("Summary:", json.dumps(summary, indent=2))

    if args.fail_on_drift and not args.offline:
        pilot = {t.strip().upper() for t in args.pilot_tickers.split(",") if t.strip()}
        failures = _check_failures(audit_rows, max_drift_pct=args.max_drift_pct, pilot_tickers=pilot)
        if failures:
            print("Drift failures:", file=sys.stderr)
            for line in failures:
                print(f"  - {line}", file=sys.stderr)
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
