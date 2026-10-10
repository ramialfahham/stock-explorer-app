"""The quality-baseline audit must re-run against identical, well-formed criteria, and report
only findings whose evidence is really in the repo."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

import pytest

import verify_quality_audit as audit

REPO = Path(__file__).resolve().parents[2]
CRITERIA = json.loads((REPO / "docs" / "quality_criteria.json").read_text(encoding="utf-8"))
WORKFLOW = (REPO / ".claude" / "workflows" / "quality-baseline-audit.js").read_text(
    encoding="utf-8"
)
# One fingerprint per criteria version. Changing a criterion without adding a new version here
# fails, so the bar cannot move silently between two audit runs that are meant to compare.
FINGERPRINTS = {1: "c8938e30eef957c5af20e883f304fcb5870c08039b4d100b93f5f6245d26bff4"}


def test_criteria_content_matches_its_version() -> None:
    canonical = json.dumps(CRITERIA["areas"], sort_keys=True, ensure_ascii=False)
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    assert digest == FINGERPRINTS[CRITERIA["version"]]


def test_criteria_have_unique_ids_and_a_rule_source_each() -> None:
    ids = [c["id"] for a in CRITERIA["areas"] for c in a["criteria"]]
    assert len(ids) == len(set(ids))
    for area in CRITERIA["areas"]:
        assert area["row"].strip() and area["paths"].strip()
        for c in area["criteria"]:
            assert c["rule"].strip() and c["source"].strip(), c["id"]


def test_criteria_workflow_and_report_cover_the_same_areas() -> None:
    keys = [a["key"] for a in CRITERIA["areas"]]
    default = re.search(r"const AREAS = .*?\[(.*?)\]", WORKFLOW).group(1)
    assert keys == re.findall(r"'([a-z]+)'", default) == list(audit.AREA_ORDER)


@pytest.fixture
def numbered(tmp_path) -> Path:
    lines = [f"line number {i:02d} of the file" for i in range(1, 21)]
    (tmp_path / "a.py").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return tmp_path


@pytest.mark.parametrize(
    "cited,found", [(10, True), (7, True), (13, True), (6, False), (14, False)]
)
def test_quote_window_is_three_lines_either_side(numbered, cited, found) -> None:
    assert audit.quote_is_present(numbered, "a.py", cited, "line number 10 of the file") is found


def test_quote_far_from_its_cited_line_is_rejected(numbered) -> None:
    assert not audit.quote_is_present(numbered, "a.py", 1, "line number 20 of the file")


def test_multi_line_quote_must_be_whole_and_in_order(numbered) -> None:
    assert audit.quote_is_present(numbered, "a.py", 10, "line number 10 of the file\n"
                                                        "line number 11 of the file")
    assert not audit.quote_is_present(numbered, "a.py", 10, "line number 11 of the file\n"
                                                            "line number 10 of the file")
    assert not audit.quote_is_present(numbered, "a.py", 10, "line number 09 of the file\n"
                                                            "line number 11 of the file")


def test_short_quote_must_be_the_whole_cited_line(tmp_path) -> None:
    (tmp_path / "b.py").write_text("try:\n    run()\nexcept:\n    pass\n", encoding="utf-8")
    assert audit.quote_is_present(tmp_path, "b.py", 3, "except:")
    assert not audit.quote_is_present(tmp_path, "b.py", 2, "except:")
    assert not audit.quote_is_present(tmp_path, "b.py", 2, "run")


def test_short_blank_or_missing_quote_is_rejected(numbered) -> None:
    assert not audit.quote_is_present(numbered, "a.py", 10, "number")
    assert not audit.quote_is_present(numbered, "a.py", 10, "  \n ")
    assert not audit.quote_is_present(numbered, "missing.py", 10, "line number 10 of the file")


def _finding(evidence: str, confirmed: bool | None) -> dict:
    return {
        "criterion_id": "HYG-1", "kind": "defect", "file": "x.py", "line": 1, "evidence": evidence,
        "rule_source": "rule", "explanation": "why", "already_tracked": "", "proposed_fix": "fix",
        "confirmed": confirmed, "verified_kind": "defect", "verify_reason": "reason",
    }


def test_report_separates_reported_refuted_no_verdict_and_missing_quotes(tmp_path) -> None:
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "quality_criteria.json").write_text('{"version": 7}', encoding="utf-8")
    (tmp_path / "x.py").write_text("a real line of code\n", encoding="utf-8")
    result = tmp_path / "result.json"
    result.write_text(json.dumps({"result": [
        {"area": "hygiene", "checked_clean": ["HYG-4"], "not_checked": [], "findings": [
            _finding("a real line of code", True),
            _finding("an invented line of code", True),
            _finding("a real line of code", False),
            _finding("a real line of code", None),
        ]},
        {"area": "docs", "error": "auditor returned nothing"},
    ]}), encoding="utf-8")
    report = tmp_path / "report.md"

    assert audit.main([str(result), "--report", str(report), "--repo", str(tmp_path)]) == 0

    text = report.read_text(encoding="utf-8")
    assert "version 7" in text
    assert "Raised 4: 1 reported, 1 refuted, 1 no verdict, 1 quote not found." in text
    assert text.count("**1. HYG-1**") == 1 and "**2." not in text
    assert "- refuted: hygiene HYG-1" in text
    assert "- no verdict: hygiene HYG-1" in text
    assert "- quote not found: hygiene HYG-1" in text
    assert "NOT AUDITED: auditor returned nothing." in text
    assert "NOT AUDITED: missing from the result." in text
