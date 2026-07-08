"""Metric layer integrity guards (the no-drift guarantee, repo-adapted).

The metric_catalogue seed is the single source of truth; int_stock__card_metrics computes each
metric once; frontend/metrics.json is generated from the seed. These tests lock those together:

  - the catalogue's metrics are all computed in the dbt model (catalogue claims nothing phantom);
  - the regenerated metrics.json matches the committed file (the frontend bridge can't silently drift);
  - the catalogue values are well-formed.

Football guards model->catalogue drift with a jinja dbt singular test; this repo's §1.1 SQL-structure
gate requires WITH-first singular tests, incompatible with column-introspection jinja — so the guard
lives here in Python (which CI already runs). Strict model->catalogue introspection (flagging a NEW
uncatalogued model column) is a Phase-2 follow-up.
"""

from __future__ import annotations

import csv
import re
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
CATALOGUE = REPO / "dbt_analytics" / "seeds" / "metric_catalogue.csv"
EXPORT = REPO / "scripts" / "export_metric_definitions_json.py"
COMMITTED_JSON = REPO / "frontend" / "metrics.json"
INT_MODEL = REPO / "dbt_analytics" / "models" / "4_intermediate" / "int_stock__card_metrics.sql"

_VALID_FORMATS = {"ratio_1", "ratio_2", "percent_1"}
_VALID_DIRECTIONS = {"higher_better", "lower_better", "neutral"}
_VALID_PERSPECTIVES = {
    "valuation",
    "profitability",
    "growth",
    "solvency",
    "liquidity",
    "cash",
    "returns",
}
_VALID_COMPANY_TYPES = {"operating", "financial", "pre_revenue"}


def _catalogue_rows() -> list[dict[str, str]]:
    with CATALOGUE.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _catalogue_ids() -> list[str]:
    return [(r.get("metric_id") or "").strip() for r in _catalogue_rows()]


def test_metric_ids_unique() -> None:
    ids = _catalogue_ids()
    assert ids
    assert len(ids) == len(set(ids)), "duplicate metric_id in catalogue"


def test_catalogue_values_well_formed() -> None:
    for row in _catalogue_rows():
        mid = row["metric_id"]
        assert row["format"] in _VALID_FORMATS, f"{mid}: bad format {row['format']!r}"
        assert row["direction"] in _VALID_DIRECTIONS, f"{mid}: bad direction {row['direction']!r}"
        assert row["perspective"] in _VALID_PERSPECTIVES, f"{mid}: bad perspective {row['perspective']!r}"
        assert (row.get("label") or "").strip(), f"{mid}: empty label"
        for field in ("calculation", "interpretation", "applicability"):
            assert (row.get(field) or "").strip(), f"{mid}: empty {field}"
        applies_to = [t.strip() for t in (row.get("applies_to") or "").split("|") if t.strip()]
        assert applies_to, f"{mid}: empty applies_to"
        assert set(applies_to) <= _VALID_COMPANY_TYPES, f"{mid}: bad applies_to {row.get('applies_to')!r}"


def test_every_catalogue_metric_is_computed_in_the_model() -> None:
    """Each catalogue metric_id must be a `... as <metric_id>` column in int_stock__card_metrics."""
    sql = INT_MODEL.read_text(encoding="utf-8")
    aliases = {m.lower() for m in re.findall(r"\bas\s+([a-z_][a-z0-9_]*)", sql, re.IGNORECASE)}
    for mid in _catalogue_ids():
        assert mid.lower() in aliases, f"catalogue metric '{mid}' is not computed in int_stock__card_metrics"


def test_frontend_metrics_match_catalogue() -> None:
    """The Streamlit app's metric list (from metrics.json) equals the catalogue's metrics."""
    import card_copy  # noqa: PLC0415

    assert set(card_copy.ALL_METRICS) == set(_catalogue_ids())


def test_regenerated_json_matches_committed() -> None:
    """Running the export must reproduce the committed frontend/metrics.json exactly."""
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "metrics.json"
        subprocess.run(
            [sys.executable, str(EXPORT), "--out", str(out)],
            check=True,
            cwd=str(REPO),
        )
        assert out.read_text(encoding="utf-8") == COMMITTED_JSON.read_text(encoding="utf-8")
