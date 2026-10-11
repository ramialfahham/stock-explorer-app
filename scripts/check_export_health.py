"""Pre-export gates for mart_stock_cards (business_summary fill on latest snapshots)."""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import duckdb

REPO_ROOT = Path(__file__).resolve().parents[1]

DEFAULT_MIN_FILL_RATE = 0.95
DEFAULT_MAX_MISSING = 5


@dataclass(frozen=True)
class ExportHealthReport:
    eligible: int
    with_business_summary: int
    missing_business_summary: int
    fill_rate: float
    missing_tickers: tuple[str, ...]


def _card_key(card: dict[str, Any]) -> tuple[str, str]:
    return (str(card["market_code"]), str(card["ticker"]))


def _has_business_summary(card: dict[str, Any]) -> bool:
    raw = card.get("business_summary")
    return bool(str(raw or "").strip())


def assess_export_health(
    cards: list[dict[str, Any]],
    *,
    min_fill_rate: float = DEFAULT_MIN_FILL_RATE,
    max_missing: int = DEFAULT_MAX_MISSING,
    required_tickers: set[tuple[str, str]] | None = None,
) -> tuple[ExportHealthReport, list[str]]:
    """Return report and failure messages (empty when healthy)."""
    eligible = [c for c in cards if c.get("is_card_eligible")]
    with_summary = [c for c in eligible if _has_business_summary(c)]
    missing = [c for c in eligible if not _has_business_summary(c)]
    total = len(eligible)
    filled = len(with_summary)
    fill_rate = filled / total if total else 0.0
    missing_tickers = tuple(
        f"{c.get('market_code')}:{c.get('ticker')}" for c in sorted(missing, key=_card_key)
    )

    report = ExportHealthReport(
        eligible=total,
        with_business_summary=filled,
        missing_business_summary=len(missing),
        fill_rate=fill_rate,
        missing_tickers=missing_tickers,
    )

    failures: list[str] = []
    if total == 0:
        failures.append("no card-eligible rows in mart_stock_cards")
        return report, failures

    if fill_rate < min_fill_rate:
        failures.append(
            f"business_summary fill rate {fill_rate:.1%} below minimum {min_fill_rate:.1%} "
            f"({filled}/{total} eligible)"
        )
    if len(missing) > max_missing:
        failures.append(
            f"{len(missing)} tickers missing business_summary exceeds max {max_missing}: "
            f"{', '.join(missing_tickers[:10])}"
            + (" …" if len(missing_tickers) > 10 else "")
        )

    if required_tickers:
        present = {_card_key(c) for c in eligible}
        for market_code, ticker in sorted(required_tickers):
            if (market_code, ticker) not in present:
                failures.append(f"required ticker missing from eligible cards: {market_code}:{ticker}")
            else:
                card = next(c for c in eligible if _card_key(c) == (market_code, ticker))
                if not _has_business_summary(card):
                    failures.append(
                        f"required ticker {market_code}:{ticker} has empty business_summary"
                    )

    return report, failures


def _load_mart_rows(conn: duckdb.DuckDBPyConnection) -> list[dict[str, Any]]:
    rows = conn.execute(
        """
        select
            market_code,
            ticker,
            is_card_eligible,
            business_summary
        from marts.mart_stock_cards
        """
    ).fetchdf()
    if rows.empty:
        return []
    return rows.to_dict(orient="records")


def _parse_required_ticker(raw: str) -> tuple[str, str]:
    market_code, ticker = raw.split(":", 1)
    return market_code.strip(), ticker.strip()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Gate mart export on business_summary fill and eligible-card sanity"
    )
    parser.add_argument(
        "--duckdb-path",
        default=str(REPO_ROOT / "storage" / "stock_data.db"),
        help="Path to DuckDB file after dbt build",
    )
    parser.add_argument(
        "--min-fill-rate",
        type=float,
        default=DEFAULT_MIN_FILL_RATE,
        help="Minimum fill rate on eligible cards (default 0.95)",
    )
    parser.add_argument(
        "--max-missing",
        type=int,
        default=DEFAULT_MAX_MISSING,
        help="Maximum tickers allowed without business_summary (default 5)",
    )
    parser.add_argument(
        "--require-ticker",
        action="append",
        default=[],
        metavar="MARKET:TICKER",
        help="Fail if ticker missing or has empty business_summary (repeatable)",
    )
    args = parser.parse_args(argv)

    db_path = Path(args.duckdb_path)
    if not db_path.exists():
        print(f"FAIL: DuckDB not found at {db_path}")
        return 1

    conn = duckdb.connect(str(db_path), read_only=True)
    try:
        cards = _load_mart_rows(conn)
    except duckdb.CatalogException as exc:
        print(f"FAIL: could not read marts.mart_stock_cards ({exc})")
        return 1
    finally:
        conn.close()

    required = {_parse_required_ticker(raw) for raw in args.require_ticker}
    report, failures = assess_export_health(
        cards,
        min_fill_rate=args.min_fill_rate,
        max_missing=args.max_missing,
        required_tickers=required or None,
    )

    print(
        "check_export_health: "
        f"eligible={report.eligible} "
        f"with_business_summary={report.with_business_summary} "
        f"fill_rate={report.fill_rate:.1%}"
    )
    if report.missing_tickers:
        print(f"  missing: {', '.join(report.missing_tickers)}")

    if failures:
        print("FAIL: export health check:")
        for msg in failures:
            print(f"  - {msg}")
        return 1

    print("check_export_health: OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
