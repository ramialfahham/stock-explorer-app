"""Compare card-eligible counts to a committed baseline (ops / CI gate)."""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import date
from pathlib import Path

import duckdb
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = REPO_ROOT / "docs" / "market_registry.yml"
DEFAULT_BASELINE_PATH = REPO_ROOT / "scripts" / "eligibility_baseline.json"


def _load_active_markets() -> list[str]:
    data = yaml.safe_load(REGISTRY_PATH.read_text(encoding="utf-8"))
    return sorted(
        m["market_code"]
        for m in data["markets"]
        if m.get("ingest_active")
    )


def _eligible_counts(conn: duckdb.DuckDBPyConnection) -> dict[str, int]:
    rows = conn.execute(
        """
        select market_code, count(*)::integer as eligible_count
        from marts.mart_stock_cards
        group by market_code
        """
    ).fetchall()
    return {str(market_code): int(count) for market_code, count in rows}


def _load_baseline(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _drop_fractions(baseline: dict, *, fail_override: float | None) -> tuple[float, float]:
    warn_fraction = float(baseline.get("warn_drop_fraction", 0.05))
    fail_fraction = fail_override
    if fail_fraction is None:
        fail_fraction = float(
            baseline.get("fail_drop_fraction", baseline.get("max_drop_fraction", 0.15))
        )
    return warn_fraction, fail_fraction


def _write_baseline(
    path: Path,
    counts: dict[str, int],
    *,
    warn_drop_fraction: float,
    fail_drop_fraction: float,
) -> None:
    payload = {
        "schema_version": 2,
        "warn_drop_fraction": warn_drop_fraction,
        "fail_drop_fraction": fail_drop_fraction,
        "max_drop_fraction": fail_drop_fraction,
        "updated_at": date.today().isoformat(),
        "note": (
            "Update after a verified healthy pipeline run: "
            "python scripts/check_eligibility_baseline.py "
            "--duckdb-path storage/stock_data.db --write-baseline"
        ),
        "markets": {
            market_code: {
                "baseline_eligible": counts.get(market_code, 0),
                "min_eligible": 5,
            }
            for market_code in _load_active_markets()
        },
        "total_baseline_eligible": sum(counts.get(m, 0) for m in _load_active_markets()),
    }
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _append_github_summary(markdown: str) -> None:
    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if not summary_path:
        return
    with open(summary_path, "a", encoding="utf-8") as handle:
        handle.write(markdown)
        if not markdown.endswith("\n"):
            handle.write("\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Detect sharp drops in card-eligible counts vs baseline"
    )
    parser.add_argument(
        "--duckdb-path",
        default=str(REPO_ROOT / "storage" / "stock_data.db"),
        help="Path to DuckDB file after dbt build",
    )
    parser.add_argument(
        "--baseline-path",
        default=str(DEFAULT_BASELINE_PATH),
        help="JSON baseline with per-market eligible counts",
    )
    parser.add_argument(
        "--max-drop-fraction",
        type=float,
        default=None,
        help="Override baseline fail_drop_fraction (default: read from baseline file)",
    )
    parser.add_argument(
        "--write-baseline",
        action="store_true",
        help="Write current eligible counts to the baseline file and exit",
    )
    args = parser.parse_args(argv)

    db_path = Path(args.duckdb_path)
    baseline_path = Path(args.baseline_path)
    if not db_path.exists():
        print(f"FAIL: DuckDB not found at {db_path}")
        return 1

    conn = duckdb.connect(str(db_path), read_only=True)
    try:
        counts = _eligible_counts(conn)
    except duckdb.CatalogException as exc:
        print(f"FAIL: could not read marts.mart_stock_cards ({exc})")
        return 1
    finally:
        conn.close()

    baseline = _load_baseline(baseline_path) if baseline_path.exists() else {}
    warn_drop_fraction, fail_drop_fraction = _drop_fractions(
        baseline,
        fail_override=args.max_drop_fraction,
    )

    if args.write_baseline:
        _write_baseline(
            baseline_path,
            counts,
            warn_drop_fraction=warn_drop_fraction,
            fail_drop_fraction=fail_drop_fraction,
        )
        print(f"Wrote baseline to {baseline_path}")
        for market_code in _load_active_markets():
            print(f"  {market_code}: {counts.get(market_code, 0)} eligible")
        print(f"  total: {sum(counts.get(m, 0) for m in _load_active_markets())}")
        return 0

    if not baseline_path.exists():
        print(f"FAIL: baseline file missing at {baseline_path}")
        return 1

    failures: list[str] = []
    warnings: list[str] = []
    summary_rows: list[str] = ["| Market | Current | Baseline | Status |", "| --- | ---: | ---: | --- |"]

    market_entries = baseline.get("markets", {})
    for market_code in _load_active_markets():
        current = counts.get(market_code, 0)
        entry = market_entries.get(market_code, {})
        baseline_count = int(entry.get("baseline_eligible", 0))
        min_eligible = int(entry.get("min_eligible", 5))
        fail_floor = int(baseline_count * (1 - fail_drop_fraction)) if baseline_count else 0
        warn_floor = int(baseline_count * (1 - warn_drop_fraction)) if baseline_count else 0

        if current < min_eligible:
            failures.append(
                f"{market_code}: eligible {current} < minimum {min_eligible}"
            )
            status = "FAIL (min)"
        elif baseline_count and current < fail_floor:
            failures.append(
                f"{market_code}: eligible {current} dropped >{fail_drop_fraction:.0%} "
                f"from baseline {baseline_count} (floor {fail_floor})"
            )
            status = "FAIL (drop)"
        elif baseline_count and current < warn_floor:
            warnings.append(
                f"{market_code}: eligible {current} dropped >{warn_drop_fraction:.0%} "
                f"from baseline {baseline_count} (warn floor {warn_floor})"
            )
            status = "WARN (drop)"
        elif baseline_count and current < baseline_count:
            warnings.append(
                f"{market_code}: eligible {current} below baseline {baseline_count}"
            )
            status = "WARN"
        else:
            status = "OK"

        summary_rows.append(
            f"| `{market_code}` | {current} | {baseline_count} | {status} |"
        )

    total_current = sum(counts.get(m, 0) for m in _load_active_markets())
    total_baseline = int(baseline.get("total_baseline_eligible", 0))
    total_fail_floor = int(total_baseline * (1 - fail_drop_fraction)) if total_baseline else 0
    total_warn_floor = int(total_baseline * (1 - warn_drop_fraction)) if total_baseline else 0
    if total_baseline and total_current < total_fail_floor:
        failures.append(
            f"total eligible {total_current} dropped >{fail_drop_fraction:.0%} "
            f"from baseline {total_baseline} (floor {total_fail_floor})"
        )
    elif total_baseline and total_current < total_warn_floor:
        warnings.append(
            f"total eligible {total_current} dropped >{warn_drop_fraction:.0%} "
            f"from baseline {total_baseline} (warn floor {total_warn_floor})"
        )

    summary_rows.extend(
        [
            "",
            f"- **Total eligible:** {total_current} (baseline {total_baseline})",
            f"- **Warn drop fraction:** {warn_drop_fraction:.0%}",
            f"- **Fail drop fraction:** {fail_drop_fraction:.0%}",
        ]
    )
    if warnings:
        summary_rows.append("- **Warnings:**")
        summary_rows.extend(f"  - {msg}" for msg in warnings)
    if failures:
        summary_rows.append("- **Failures:**")
        summary_rows.extend(f"  - {msg}" for msg in failures)

    _append_github_summary("## Eligibility baseline check\n\n" + "\n".join(summary_rows))

    for msg in warnings:
        print(f"WARN: {msg}")

    if failures:
        print("FAIL: eligibility baseline check:")
        for msg in failures:
            print(f"  - {msg}")
        return 1

    print("check_eligibility_baseline: OK")
    print(f"  total eligible: {total_current} (baseline {total_baseline})")
    for market_code in _load_active_markets():
        print(f"  {market_code}: {counts.get(market_code, 0)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
