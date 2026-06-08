"""Summarize ineligible tickers and missing-metric patterns from QA mart."""

from __future__ import annotations

import argparse
import os
import sys
from collections import Counter
from pathlib import Path

import duckdb
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = REPO_ROOT / "docs" / "market_registry.yml"


def _load_active_markets() -> list[str]:
    data = yaml.safe_load(REGISTRY_PATH.read_text(encoding="utf-8"))
    return sorted(
        m["market_code"]
        for m in data["markets"]
        if m.get("ingest_active")
    )


def _append_github_summary(markdown: str) -> None:
    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if not summary_path:
        return
    with open(summary_path, "a", encoding="utf-8") as handle:
        handle.write(markdown)
        if not markdown.endswith("\n"):
            handle.write("\n")


def _metric_labels(raw: object) -> list[str]:
    if raw is None:
        return []
    if isinstance(raw, (list, tuple)):
        return [str(item) for item in raw]
    text = str(raw).strip()
    if text.startswith("[") and text.endswith("]"):
        inner = text[1:-1].strip()
        if not inner:
            return []
        return [part.strip().strip("'\"") for part in inner.split(",")]
    return [text] if text else []


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Report eligibility gaps and near-miss patterns from DuckDB QA mart"
    )
    parser.add_argument(
        "--duckdb-path",
        default=str(REPO_ROOT / "storage" / "stock_data.db"),
        help="Path to DuckDB file after dbt build",
    )
    parser.add_argument(
        "--fail-on-empty-eligible",
        action="store_true",
        help="Exit non-zero if any active market has zero eligible rows in mart_stock_cards",
    )
    args = parser.parse_args(argv)

    db_path = Path(args.duckdb_path)
    if not db_path.exists():
        print(f"FAIL: DuckDB not found at {db_path}")
        return 1

    conn = duckdb.connect(str(db_path), read_only=True)
    try:
        eligible_counts = {
            str(row[0]): int(row[1])
            for row in conn.execute(
                """
                select market_code, count(*)::integer
                from marts.mart_stock_cards
                group by market_code
                """
            ).fetchall()
        }
        gap_rows = conn.execute(
            """
            select market_code, ticker, missing_metrics
            from marts.mart_stock_eligibility_gaps
            """
        ).fetchall()
    except duckdb.CatalogException as exc:
        print(f"FAIL: could not read eligibility marts ({exc})")
        return 1
    finally:
        conn.close()

    failures: list[str] = []
    summary_lines = [
        "## Eligibility gaps summary",
        "",
        "| Market | Eligible | Ineligible | Near-miss (1 missing) | Top missing metric |",
        "| --- | ---: | ---: | ---: | --- |",
    ]

    for market_code in _load_active_markets():
        eligible = eligible_counts.get(market_code, 0)
        market_gaps = [row for row in gap_rows if str(row[0]) == market_code]
        ineligible = len(market_gaps)
        near_miss = 0
        metric_counter: Counter[str] = Counter()
        for _, _, missing_raw in market_gaps:
            labels = _metric_labels(missing_raw)
            if len(labels) == 1:
                near_miss += 1
            metric_counter.update(labels)
        top_missing = metric_counter.most_common(1)[0][0] if metric_counter else "—"

        if args.fail_on_empty_eligible and eligible == 0:
            failures.append(f"{market_code}: zero eligible rows in mart_stock_cards")

        summary_lines.append(
            f"| `{market_code}` | {eligible} | {ineligible} | {near_miss} | {top_missing} |"
        )
        print(
            f"{market_code}: eligible={eligible} ineligible={ineligible} "
            f"near_miss={near_miss} top_missing={top_missing}"
        )

    _append_github_summary("\n".join(summary_lines))

    if failures:
        print("FAIL: eligibility gaps check:")
        for msg in failures:
            print(f"  - {msg}")
        return 1

    print("check_eligibility_gaps: OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
