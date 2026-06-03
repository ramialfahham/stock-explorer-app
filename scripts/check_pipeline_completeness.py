"""Completeness gates for Tier C pipeline (see docs/data_contract.md)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import duckdb
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = REPO_ROOT / "docs" / "market_registry.yml"
RAW_ROOT = REPO_ROOT / "storage" / "raw"
SEEDS_ROOT = REPO_ROOT / "storage" / "seeds"

FAIL_ELIGIBLE_THRESHOLD = 5
WARN_ELIGIBLE_THRESHOLD = 20


def _load_active_markets() -> list[str]:
    data = yaml.safe_load(REGISTRY_PATH.read_text(encoding="utf-8"))
    return sorted(
        m["market_code"]
        for m in data["markets"]
        if m.get("ingest_active")
    )


def _count_seed_rows(market_code: str) -> int:
    seed_path = SEEDS_ROOT / market_code / "constituents.csv"
    if not seed_path.exists():
        return 0
    lines = seed_path.read_text(encoding="utf-8").strip().splitlines()
    return max(0, len(lines) - 1)


def _eligible_count(conn: duckdb.DuckDBPyConnection, market_code: str) -> int | None:
    try:
        row = conn.execute(
            """
            select count(*)::integer
            from marts.mart_stock_cards
            where market_code = ?
              and is_card_eligible
            """,
            [market_code],
        ).fetchone()
        return int(row[0]) if row else 0
    except duckdb.CatalogException:
        return None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check pipeline completeness gates")
    parser.add_argument(
        "--duckdb-path",
        default=str(REPO_ROOT / "storage" / "stock_data.db"),
        help="Path to DuckDB file after dbt build",
    )
    args = parser.parse_args(argv)

    failures: list[str] = []
    warnings: list[str] = []

    for market_code in _load_active_markets():
        seed_rows = _count_seed_rows(market_code)
        if seed_rows == 0:
            failures.append(f"{market_code}: constituent seed missing or empty")

        fundamentals_path = RAW_ROOT / market_code / "yf_fundamentals.parquet"
        if not fundamentals_path.exists():
            failures.append(f"{market_code}: yf_fundamentals.parquet missing after ingest")

    db_path = Path(args.duckdb_path)
    if db_path.exists():
        conn = duckdb.connect(str(db_path), read_only=True)
        try:
            for market_code in _load_active_markets():
                eligible = _eligible_count(conn, market_code)
                if eligible is None:
                    warnings.append(
                        f"{market_code}: marts.mart_stock_cards not found (run dbt build first)"
                    )
                    continue
                if eligible < FAIL_ELIGIBLE_THRESHOLD:
                    failures.append(
                        f"{market_code}: card-eligible count {eligible} < {FAIL_ELIGIBLE_THRESHOLD}"
                    )
                elif eligible < WARN_ELIGIBLE_THRESHOLD:
                    warnings.append(
                        f"{market_code}: card-eligible count {eligible} < {WARN_ELIGIBLE_THRESHOLD}"
                    )
        finally:
            conn.close()
    else:
        warnings.append(f"DuckDB not found at {db_path}; skipped eligible-count checks")

    for msg in warnings:
        print(f"WARN: {msg}")

    if failures:
        print("FAIL: completeness gates not met:")
        for msg in failures:
            print(f"  - {msg}")
        return 1

    print("check_pipeline_completeness: OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
