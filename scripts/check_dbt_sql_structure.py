"""Project-specific SQL structure checks from docs/engineering_standards.md §1.1.

Supplements SQLFluff (structure.subquery, layout). Covers rules SQLFluff cannot express:
- Top-level WITH required
- No scalar subqueries in the SELECT list
- Each ref()/source() must appear in an import-style CTE (from {{ ref ... }} in a CTE body)
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SQL_PATHS = (
    REPO_ROOT / "dbt_analytics" / "models",
    REPO_ROOT / "dbt_analytics" / "tests",
)

JINJA_LINE = re.compile(r"^\s*{%.*?%}\s*$", re.DOTALL)
FROM_INLINE_SUBQUERY = re.compile(r"\bfrom\s*\(\s*select\b", re.IGNORECASE)
SCALAR_SUBQUERY_IN_SELECT = re.compile(
    r"(?is)^\s*select\s+.*?\(\s*select\s+",
)
REF_OR_SOURCE = re.compile(
    r"""ref\s*\(\s*['"][^'"]+['"]\s*\)|source\s*\(\s*['"][^'"]+['"]\s*\)""",
    re.IGNORECASE,
)
IMPORT_CTE_FROM_REF = re.compile(
    r"""from\s+\{\{\s*(?:ref|source)\s*\(""",
    re.IGNORECASE,
)


def _strip_jinja(content: str) -> str:
    lines = [line for line in content.splitlines() if not JINJA_LINE.match(line)]
    return "\n".join(lines)


def _strip_leading_line_comments(sql: str) -> str:
    """Remove leading -- comment lines (§1.2 allows why-comments before WITH)."""
    body_lines: list[str] = []
    for line in sql.splitlines():
        if line.strip().startswith("--"):
            continue
        body_lines.append(line)
    return "\n".join(body_lines).strip()


def _check_file(path: Path, errors: list[str]) -> None:
    rel = path.relative_to(REPO_ROOT).as_posix()
    raw = path.read_text(encoding="utf-8")
    sql = _strip_jinja(raw).strip()
    if not sql:
        return

    sql_body = _strip_leading_line_comments(sql)

    if not re.match(r"(?is)^with\s+", sql_body):
        errors.append(f"{rel}: must start with a WITH clause (§1.1)")

    if FROM_INLINE_SUBQUERY.search(sql):
        errors.append(f"{rel}: forbidden inline subquery in FROM (§1.1)")

    if SCALAR_SUBQUERY_IN_SELECT.search(sql):
        errors.append(
            f"{rel}: forbidden scalar subquery in SELECT list; use CTEs (§1.1)"
        )

    if REF_OR_SOURCE.search(raw) and not IMPORT_CTE_FROM_REF.search(sql_body):
        errors.append(
            f"{rel}: ref()/source() must appear inside import CTEs "
            "(from {{{{ ref(...) }}}}) (§1.1)"
        )


def main() -> int:
    errors: list[str] = []
    for root in SQL_PATHS:
        if not root.is_dir():
            continue
        for sql_path in sorted(root.rglob("*.sql")):
            _check_file(sql_path, errors)

    if errors:
        print("dbt SQL structure checks failed:")
        for err in errors:
            print(f" - {err}")
        return 1

    print("dbt SQL structure checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
