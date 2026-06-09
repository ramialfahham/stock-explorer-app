"""Pre-export gates for mart_stock_cards (business_summary fill on latest snapshots)."""

from __future__ import annotations

import argparse
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import duckdb
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = REPO_ROOT / "docs" / "market_registry.yml"

DEFAULT_MIN_FILL_RATE = 0.95
DEFAULT_MAX_MISSING = 5


@dataclass(frozen=True)
class ExportHealthReport:
    deduped_eligible: int
    with_business_summary: int
    missing_business_summary: int
    fill_rate: float
    missing_tickers: tuple[str, ...]


def _card_key(card: dict[str, Any]) -> tuple[str, str]:
    return (str(card["market_code"]), str(card["ticker"]))


def _snapshot_sort_key(card: dict[str, Any]) -> str:
    raw = card.get("snapshot_date")
    if raw is None:
        return ""
    return str(raw)[:10]


def _has_business_summary(card: dict[str, Any]) -> bool:
    raw = card.get("business_summary")
    return bool(str(raw or "").strip())


def dedupe_to_latest_snapshot(cards: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Keep one row per (market_code, ticker) — latest snapshot_date wins."""
    latest: dict[tuple[str, str], dict[str, Any]] = {}
    for card in cards:
        key = _card_key(card)
        prev = latest.get(key)
        if prev is None:
            latest[key] = card
            continue
        card_key = _snapshot_sort_key(card)
        prev_key = _snapshot_sort_key(prev)
        if card_key > prev_key:
            winner, loser = card, prev
        elif card_key < prev_key:
            winner, loser = prev, card
        else:
            winner, loser = prev, card
        merged = dict(winner)
        if not _has_business_summary(merged) and _has_business_summary(loser):
            merged["business_summary"] = loser.get("business_summary")
        latest[key] = merged
    return list(latest.values())


def assess_export_health(
    cards: list[dict[str, Any]],
    *,
    min_fill_rate: float = DEFAULT_MIN_FILL_RATE,
    max_missing: int = DEFAULT_MAX_MISSING,
    required_tickers: set[tuple[str, str]] | None = None,
) -> tuple[ExportHealthReport, list[str]]:
    """Return report and failure messages (empty when healthy)."""
    eligible = [c for c in cards if c.get("is_card_eligible")]
    deduped = dedupe_to_latest_snapshot(eligible)
    with_summary = [c for c in deduped if _has_business_summary(c)]
    missing = [c for c in deduped if not _has_business_summary(c)]
    total = len(deduped)
    filled = len(with_summary)
    fill_rate = filled / total if total else 0.0
    missing_tickers = tuple(
        f"{c.get('market_code')}:{c.get('ticker')}" for c in sorted(missing, key=_card_key)
    )

    report = ExportHealthReport(
        deduped_eligible=total,
        with_business_summary=filled,
        missing_business_summary=len(missing),
        fill_rate=fill_rate,
        missing_tickers=missing_tickers,
    )

    failures: list[str] = []
    if total == 0:
        failures.append("no deduped card-eligible rows in mart_stock_cards")
        return report, failures

    if fill_rate < min_fill_rate:
        failures.append(
            f"business_summary fill rate {fill_rate:.1%} below minimum {min_fill_rate:.1%} "
            f"({filled}/{total} deduped eligible)"
        )
    if len(missing) > max_missing:
        failures.append(
            f"{len(missing)} tickers missing business_summary exceeds max {max_missing}: "
            f"{', '.join(missing_tickers[:10])}"
            + (" …" if len(missing_tickers) > 10 else "")
        )

    if required_tickers:
        present = {_card_key(c) for c in deduped}
        for market_code, ticker in sorted(required_tickers):
            if (market_code, ticker) not in present:
                failures.append(f"required ticker missing from deduped eligible: {market_code}:{ticker}")
            else:
                card = next(c for c in deduped if _card_key(c) == (market_code, ticker))
                if not _has_business_summary(card):
                    failures.append(
                        f"required ticker {market_code}:{ticker} has empty business_summary"
                    )

    return report, failures


def _load_active_markets() -> list[str]:
    data = yaml.safe_load(REGISTRY_PATH.read_text(encoding="utf-8"))
    return sorted(
        m["market_code"]
        for m in data["markets"]
        if m.get("ingest_active")
    )


def _load_mart_rows(conn: duckdb.DuckDBPyConnection) -> list[dict[str, Any]]:
    rows = conn.execute(
        """
        select
            market_code,
            ticker,
            is_card_eligible,
            business_summary,
            snapshot_date
        from marts.mart_stock_cards
        """
    ).fetchdf()
    if rows.empty:
        return []
    return rows.to_dict(orient="records")


def _append_github_summary(markdown: str) -> None:
    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if not summary_path:
        return
    with open(summary_path, "a", encoding="utf-8") as handle:
        handle.write(markdown)
        if not markdown.endswith("\n"):
            handle.write("\n")


def _parse_required_ticker(raw: str) -> tuple[str, str]:
    market_code, ticker = raw.split(":", 1)
    return market_code.strip(), ticker.strip()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Gate mart export on business_summary fill and deduped eligible sanity"
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
        help="Minimum fill rate on deduped eligible cards (default 0.95)",
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

    summary_lines = [
        "## Export health check",
        "",
        f"- **Deduped eligible:** {report.deduped_eligible}",
        f"- **With business_summary:** {report.with_business_summary}",
        f"- **Fill rate:** {report.fill_rate:.1%}",
        f"- **Min fill rate:** {args.min_fill_rate:.1%}",
        f"- **Max missing allowed:** {args.max_missing}",
    ]
    if report.missing_tickers:
        summary_lines.append("- **Missing business_summary:**")
        summary_lines.extend(f"  - `{ticker}`" for ticker in report.missing_tickers[:20])
        if len(report.missing_tickers) > 20:
            summary_lines.append(f"  - … and {len(report.missing_tickers) - 20} more")
    _append_github_summary("\n".join(summary_lines))

    print(
        "check_export_health: "
        f"deduped_eligible={report.deduped_eligible} "
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
