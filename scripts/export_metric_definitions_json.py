#!/usr/bin/env python3
"""Export the frontend metric-definitions JSON from the metric_catalogue seed.

The seed (dbt_analytics/seeds/metric_catalogue.csv) is the single source of truth for every
card metric. This script reads it and writes frontend/metrics.json — the display definitions
the Streamlit app binds to (label, format, direction, group/tier/order, benchmarkable, the
basis column, and the plain-language copy). The catalogue is never modified here.

Output must stay byte-identical unless a definition deliberately changes; tests/test_metric_definitions.py
regenerates and asserts equality against the committed file (the no-drift lock).
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

# Frontend-facing fields, in output order. (base_relation / numerator_expr / denominator_expr
# are the dbt-side formula spec and are intentionally NOT exported to the UI.)
_TEXT_FIELDS = (
    "label",
    "description",
    "calculation",
    "interpretation",
    "applicability",
    "format",
    "perspective",
    "direction",
    "basis_column",
    "gloss",
    "analogy",
    "learn",
)


def _truthy(value: str | None) -> bool:
    return (value or "").strip().lower() in ("true", "1", "yes")


def _int_or_none(value: str | None) -> int | None:
    value = (value or "").strip()
    return int(value) if value else None


def build_defs(catalogue_path: Path) -> list[dict[str, object]]:
    """Ordered list of metric display definitions from the catalogue SSoT."""
    rows: list[dict[str, object]] = []
    seen: set[str] = set()
    with catalogue_path.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            metric_id = (row.get("metric_id") or "").strip()
            if not metric_id:
                continue
            if metric_id in seen:
                raise SystemExit(f"metric_catalogue: duplicate metric_id '{metric_id}'")
            seen.add(metric_id)
            entry: dict[str, object] = {"metric_id": metric_id}
            for field in _TEXT_FIELDS:
                entry[field] = (row.get(field) or "").strip()
            entry["importance_tier"] = _int_or_none(row.get("importance_tier"))
            entry["display_order"] = _int_or_none(row.get("display_order"))
            entry["benchmarkable"] = _truthy(row.get("benchmarkable"))
            rows.append(entry)
    if not rows:
        raise SystemExit("metric_catalogue: no metric rows found")
    rows.sort(key=lambda r: (r["display_order"] is None, r["display_order"]))
    return rows


def render(defs: list[dict[str, object]]) -> str:
    return json.dumps({"metrics": defs}, ensure_ascii=False, indent=2) + "\n"


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--catalogue",
        type=Path,
        default=root / "dbt_analytics" / "seeds" / "metric_catalogue.csv",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=root / "frontend" / "metrics.json",
    )
    args = parser.parse_args()

    defs = build_defs(args.catalogue)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(render(defs), encoding="utf-8")
    print(f"Wrote {len(defs)} metric definitions to {args.out}")


if __name__ == "__main__":
    main()
