"""Check a quality-baseline audit run and write its report.

Reads the result the `quality-baseline-audit` workflow (`.claude/workflows/`) returns: the
workflow's output JSON, or its bare result list. Confirms that every finding's verbatim evidence
appears, whole and in order, within three lines of its cited line (a quote under ten normalised
characters must be the whole cited line), and writes a Markdown report
numbering each finding. Only skeptic-confirmed findings whose quote is found are reported; the
rest are listed under "Not reported" as refuted, no verdict, or quote not found, because the
audit's guarantee is evidence, not assertion. Criteria: `docs/quality_criteria.json`.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AREA_ORDER = ("ingestion", "dbt", "export", "frontend", "docs", "hygiene", "guardrails")
KIND_TITLES = {
    "defect": "Defect",
    "unenforced_standard": "Holds, but unenforced",
    "documented_decision": "Documented decision worth revisiting",
    "proposed_rule": "Proposed rule (no written rule; owner decides)",
}
QUOTE_WINDOW = 3
# A quote this short ("}", "return x") would match almost any window, so it must be the whole
# cited line rather than any text near it.
MIN_QUOTE_CHARS = 10


def _normalise(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def quote_is_present(repo: Path, file: str, line: int, evidence: str) -> bool:
    path = repo / file
    quote = _normalise(evidence)
    if not path.is_file() or not quote:
        return False
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    if len(quote) < MIN_QUOTE_CHARS:
        return 0 < line <= len(lines) and _normalise(lines[line - 1]) == quote
    lo = max(0, line - 1 - QUOTE_WINDOW)
    hi = min(len(lines), line + QUOTE_WINDOW + evidence.count("\n"))
    return quote in _normalise(" ".join(lines[lo:hi]))


def load_result(path: Path) -> list[dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return data["result"] if isinstance(data, dict) else data


def numbered_findings(areas: list[dict], repo: Path) -> list[dict]:
    by_area = {a["area"]: a for a in areas}
    rows = []
    for key in AREA_ORDER:
        findings = by_area.get(key, {}).get("findings") or []
        for kind in KIND_TITLES:
            for f in findings:
                if (f.get("verified_kind") or f["kind"]) == kind:
                    present = quote_is_present(repo, f["file"], f["line"], f["evidence"])
                    rows.append({**f, "area": key, "kind": kind, "quote_ok": present})
    for n, row in enumerate(rows, 1):
        row["n"] = n
    return rows


def status(row: dict) -> str:
    if row["confirmed"] is None:
        return "no verdict"
    if not row["confirmed"]:
        return "refuted"
    return "reported" if row["quote_ok"] else "quote not found"


def render(areas: list[dict], rows: list[dict], criteria_version: object) -> str:
    kept = [r for r in rows if status(r) == "reported"]
    counts = {s: sum(1 for r in rows if status(r) == s)
              for s in ("reported", "refuted", "no verdict", "quote not found")}
    out = [
        "# Quality baseline audit",
        "",
        f"Criteria: `docs/quality_criteria.json` version {criteria_version}.",
        f"Raised {len(rows)}: " + ", ".join(f"{n} {s}" for s, n in counts.items()) + ".",
        "",
    ]
    by_area = {a["area"]: a for a in areas}
    for key in AREA_ORDER:
        area = by_area.get(key)
        area_rows = [r for r in kept if r["area"] == key]
        out += [f"## {key} ({len(area_rows)})", ""]
        if area is None or area.get("error"):
            reason = area.get("error") if area else "missing from the result"
            out += [f"NOT AUDITED: {reason}.", ""]
            continue
        if area.get("verify_missing"):
            out += ["The skeptic returned nothing for this area; its findings have no verdict.", ""]
        for kind, title in KIND_TITLES.items():
            group = [r for r in area_rows if r["kind"] == kind]
            if group:
                out += [f"### {title}", ""]
            for r in group:
                tracked = r.get("already_tracked")
                tracked = f" (tracked: {tracked})" if tracked else ""
                out += [
                    f"**{r['n']}. {r['criterion_id']}** `{r['file']}:{r['line']}`{tracked}", "",
                    "```", r["evidence"], "```", "",
                    f"- Rule: {r['rule_source']}",
                    f"- Finding: {r['explanation']}",
                    f"- Proposed fix: {r['proposed_fix']}",
                    f"- Skeptic: {r['verify_reason']}",
                    "",
                ]
        out += ["Checked clean:", ""] + [f"- {c}" for c in area.get("checked_clean", [])] + [""]
        out += ["Not checked:", ""] + [f"- {c}" for c in area.get("not_checked", [])] + [""]
    out += ["## Not reported", ""]
    for r in rows:
        if status(r) != "reported":
            where = f"{r['area']} {r['criterion_id']} `{r['file']}:{r['line']}`"
            out.append(f"- {status(r)}: {where} -- {r['verify_reason']}")
    return "\n".join(out) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("result", type=Path, help="the workflow's output JSON")
    parser.add_argument("--report", type=Path, required=True, help="Markdown report to write")
    parser.add_argument("--repo", type=Path, default=ROOT)
    args = parser.parse_args(argv)

    areas = load_result(args.result)
    rows = numbered_findings(areas, args.repo)
    criteria_path = args.repo / "docs" / "quality_criteria.json"
    criteria = json.loads(criteria_path.read_text(encoding="utf-8"))
    args.report.write_text(render(areas, rows, criteria.get("version")), encoding="utf-8")

    counts = {s: sum(1 for r in rows if status(r) == s)
              for s in ("reported", "refuted", "no verdict", "quote not found")}
    print(f"{len(rows)} raised: " + ", ".join(f"{n} {s}" for s, n in counts.items()))
    print(f"Wrote {args.report}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
