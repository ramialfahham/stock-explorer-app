#!/usr/bin/env python3
"""Compare mart_stock_cards metrics to fresh yfinance, recomputed via dbt (see docs/metric_audit.md).

Metric-layer Phase 2: no Python path produces a card value. To validate the mart, this fetches
fresh fundamentals for a sample, lands them as a temporary raw parquet set, rebuilds
int_stock__card_metrics through dbt into a throwaway DuckDB, and compares those dbt-computed
values to the mart. The dbt model is the single source of every stored metric; the learn
panel's playgrounds (frontend/metric_school.py) do the catalogue's arithmetic on numbers the
user types and never write one.
Offline mode (CI smoke) skips the live fetch + dbt rebuild and reports only mart-side facts.
"""

from __future__ import annotations

import argparse
import csv
import json
import random
import shutil
import subprocess
import sys
import tempfile
from collections import defaultdict
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
from ingestion.yfinance.symbols import to_yfinance_ticker

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
    "dividend_yield_pct",
    "is_card_eligible",
)
METRIC_KEYS = (
    "forward_pe",
    "ebit_margin_pct",
    "revenue_growth_yoy_pct",
    "net_debt_to_ebitda",
    "fcf_margin_pct",
    "dividend_yield_pct",
)

# Raw fundamentals parquet schema (must match dbt sources.yml yf_fundamentals).
FUNDAMENTALS_COLUMNS = (
    "market_code", "ticker", "snapshot_date",
    "info_forward_pe", "info_operating_margins", "info_revenue_growth",
    "info_net_debt", "info_total_debt", "info_total_cash", "info_ebitda",
    "info_sector", "info_currency", "info_long_name", "info_business_summary", "info_founded_year",
    "stmt_total_revenue", "stmt_free_cash_flow", "stmt_fiscal_period_end", "stmt_currency",
    "qtr_operating_income_0", "qtr_operating_income_1", "qtr_operating_income_2", "qtr_operating_income_3",
    "qtr_total_revenue_0", "qtr_total_revenue_1", "qtr_total_revenue_2", "qtr_total_revenue_3",
    "qtr_operating_revenue_0", "qtr_operating_revenue_1", "qtr_operating_revenue_2", "qtr_operating_revenue_3",
    "qtr_operating_expense_0", "qtr_operating_expense_1", "qtr_operating_expense_2", "qtr_operating_expense_3",
    "stmt_operating_income", "stmt_operating_revenue", "stmt_operating_expense",
    "stmt_stockholders_equity", "stmt_total_debt", "stmt_current_assets",
    "stmt_current_liabilities", "stmt_cash_and_equivalents", "stmt_tangible_book_value",
    "stmt_total_assets",
    "stmt_operating_cash_flow", "stmt_capital_expenditure", "stmt_interest_expense",
    "stmt_net_income", "stmt_net_income_common", "info_dividend_yield", "info_payout_ratio",
)
INT_MODEL_RELATION = "intermediate.int_stock__card_metrics"


def pct_drift(mart: float | None, fresh: float | None) -> float | None:
    """Signed percentage difference of the mart value from the freshly recomputed value."""
    if mart is None or fresh is None or fresh == 0:
        return None
    return (mart - fresh) / abs(fresh) * 100


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
    import os

    from dotenv import load_dotenv
    from supabase import create_client

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


def _fetch_live_raw(market_code: str, ticker: str, markets: dict) -> dict | None:
    market = markets.get(market_code)
    if market is None:
        return None
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


def _build_fresh_metrics_via_dbt(raw_rows: list[dict]) -> dict[tuple[str, str], dict]:
    """Land fresh raw, rebuild int_stock__card_metrics via dbt, return {(market, ticker): metrics}.

    Returns {} (and warns) if the rebuild fails — the audit then reports no drift for those rows.
    """
    if not raw_rows:
        return {}

    import pandas as pd

    by_market: dict[str, list[dict]] = defaultdict(list)
    for row in raw_rows:
        by_market[row["market_code"]].append(row)

    with tempfile.TemporaryDirectory(prefix="metric_audit_") as tmp_name:
        tmp = Path(tmp_name)
        raw_root = tmp / "raw"
        for market_code, rows in by_market.items():
            market_dir = raw_root / market_code
            market_dir.mkdir(parents=True)
            funds = pd.DataFrame(rows).reindex(columns=list(FUNDAMENTALS_COLUMNS))
            funds.to_parquet(market_dir / "yf_fundamentals.parquet", index=False)
            consts = pd.DataFrame(
                [
                    {
                        "market_code": market_code,
                        "ticker": row["ticker"],
                        "company_name": row.get("info_long_name") or row["ticker"],
                        "refreshed_at": "",
                        "source": "audit",
                        "ingested_at": "",
                    }
                    for row in rows
                ]
            )
            consts.to_parquet(market_dir / "yf_constituents.parquet", index=False)

        duckdb_path = tmp / "audit.duckdb"
        profiles_dir = tmp / "profiles"
        profiles_dir.mkdir()
        (profiles_dir / "profiles.yml").write_text(
            "dbt_analytics:\n"
            "  target: dev\n"
            "  outputs:\n"
            "    dev:\n"
            "      type: duckdb\n"
            f"      path: {duckdb_path.as_posix()}\n"
            "      threads: 4\n",
            encoding="utf-8",
        )

        dbt_exe = shutil.which("dbt") or "dbt"
        cmd = [
            dbt_exe, "run", "--select", "+int_stock__card_metrics",
            "--project-dir", str(ROOT / "dbt_analytics"),
            "--profiles-dir", str(profiles_dir),
            "--vars", json.dumps(
                {"raw_path": raw_root.as_posix(), "active_market_codes": sorted(by_market)}
            ),
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            tail = "\n".join((result.stdout or "").splitlines()[-10:])
            print(f"  warning: dbt rebuild failed (exit {result.returncode}):\n{tail}", file=sys.stderr)
            return {}

        conn = duckdb.connect(str(duckdb_path), read_only=True)
        try:
            cols = ", ".join(("market_code", "ticker", *METRIC_KEYS))
            rows = conn.execute(f"select {cols} from {INT_MODEL_RELATION}").fetchall()
            names = [desc[0] for desc in conn.description]
        finally:
            conn.close()

    fresh: dict[tuple[str, str], dict] = {}
    for row in rows:
        record = dict(zip(names, row, strict=True))
        fresh[(record["market_code"], record["ticker"])] = record
    return fresh


def _base_audit_row(mart: dict) -> dict:
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
    return out


def _audit_row(mart: dict, fresh: dict | None, *, fetch_ok: bool) -> dict:
    out = _base_audit_row(mart)
    out["live_fetch_ok"] = fetch_ok
    out["dbt_rebuild_ok"] = fresh is not None
    if fresh is None:
        return out
    for metric in METRIC_KEYS:
        out[f"fresh_{metric}"] = fresh.get(metric)
        out[f"drift_pct_{metric}"] = pct_drift(mart.get(metric), fresh.get(metric))
    return out


def _summarize(rows: list[dict]) -> dict:
    summary: dict[str, object] = {
        "rows": len(rows),
        "live_fetch_ok": sum(1 for r in rows if r.get("live_fetch_ok")),
        "dbt_rebuild_ok": sum(1 for r in rows if r.get("dbt_rebuild_ok")),
        "business_summary_fill_rate": round(
            sum(1 for r in rows if r.get("business_summary_present")) / max(len(rows), 1),
            3,
        ),
    }
    for metric in METRIC_KEYS:
        drifts = [r[f"drift_pct_{metric}"] for r in rows if r.get(f"drift_pct_{metric}") is not None]
        if drifts:
            summary[f"median_drift_pct_{metric}"] = round(sorted(drifts)[len(drifts) // 2], 2)
            summary[f"max_drift_pct_{metric}"] = round(max(drifts, key=abs), 2)
    return summary


def _write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        return
    fieldnames: list[str] = []
    for row in rows:
        for key in row:
            if key not in fieldnames:
                fieldnames.append(key)
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
            if drift is not None and abs(drift) > max_drift_pct:
                failures.append(
                    f"{row['ticker']} {metric}: drift {drift:.1f}% "
                    f"(mart={row.get(f'mart_{metric}')} fresh={row.get(f'fresh_{metric}')})"
                )
    return failures


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Audit mart metrics vs fresh yfinance recomputed via dbt")
    parser.add_argument("--source", choices=("duckdb", "supabase"), default="duckdb")
    parser.add_argument("--duckdb-path", default=str(ROOT / "storage" / "stock_data.db"))
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
        help="Skip live yfinance fetch + dbt rebuild (CI mode); report mart-side facts only",
    )
    parser.add_argument("--output-dir", default=str(ROOT / "storage" / "audit"))
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

    if args.offline:
        audit_rows = [_base_audit_row(mart) for mart in sample]
    else:
        markets = _market_lookup()
        fetched: dict[tuple[str, str], bool] = {}
        raw_rows: list[dict] = []
        for mart in sample:
            key = (mart["market_code"], mart["ticker"])
            raw = _fetch_live_raw(mart["market_code"], mart["ticker"], markets)
            fetched[key] = raw is not None
            if raw is not None:
                raw_rows.append(raw)
        fresh_metrics = _build_fresh_metrics_via_dbt(raw_rows)
        audit_rows = [
            _audit_row(
                mart,
                fresh_metrics.get((mart["market_code"], mart["ticker"])),
                fetch_ok=fetched[(mart["market_code"], mart["ticker"])],
            )
            for mart in sample
        ]

    summary = _summarize(audit_rows)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    csv_path = output_dir / f"metric_audit_{stamp}.csv"
    json_path = output_dir / f"metric_audit_{stamp}.json"
    _write_csv(csv_path, audit_rows)
    json_path.write_text(
        json.dumps({"summary": summary, "rows": audit_rows}, indent=2, default=str),
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
