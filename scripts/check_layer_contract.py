"""Enforce dbt layer contract rules from docs/layering.md."""

from __future__ import annotations

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DBT_MODELS = REPO_ROOT / "dbt_analytics" / "models"
CORE_DIR = DBT_MODELS / "3_core"
INTERMEDIATE_DIR = DBT_MODELS / "4_intermediate"
STAGING_DIR = DBT_MODELS / "1_staging"

INTERMEDIATE_FORBIDDEN_MART_REF = re.compile(
    r"""ref\s*\(\s*['"]mart_""",
    re.IGNORECASE,
)

CORE_FORBIDDEN_PATTERNS = (
    re.compile(r"""ref\(\s*['"]stg_""", re.IGNORECASE),
    re.compile(r"\bunion_all\s*\(", re.IGNORECASE),
)


def check_core_forbidden_patterns(errors: list[str]) -> None:
    if not CORE_DIR.is_dir():
        return
    for sql_path in sorted(CORE_DIR.rglob("*.sql")):
        content = sql_path.read_text(encoding="utf-8")
        for pattern in CORE_FORBIDDEN_PATTERNS:
            if pattern.search(content):
                rel = sql_path.relative_to(REPO_ROOT).as_posix()
                errors.append(
                    f"{rel}: contains forbidden pattern in core: {pattern.pattern}"
                )


def check_intermediate_no_mart_refs(errors: list[str]) -> None:
    if not INTERMEDIATE_DIR.is_dir():
        return
    for sql_path in sorted(INTERMEDIATE_DIR.rglob("*.sql")):
        content = sql_path.read_text(encoding="utf-8")
        if INTERMEDIATE_FORBIDDEN_MART_REF.search(content):
            rel = sql_path.relative_to(REPO_ROOT).as_posix()
            errors.append(
                f"{rel}: intermediate layer must not ref() mart_* models "
                f"(matched {INTERMEDIATE_FORBIDDEN_MART_REF.pattern})"
            )


def check_staging_layout(errors: list[str]) -> None:
    if not STAGING_DIR.is_dir():
        return
    for path in sorted(STAGING_DIR.glob("*.sql")):
        rel = path.relative_to(REPO_ROOT).as_posix()
        errors.append(
            f"{rel}: staging SQL must live under 1_staging/<source>/, "
            "not directly under 1_staging/."
        )


def main() -> int:
    errors: list[str] = []
    check_core_forbidden_patterns(errors)
    check_intermediate_no_mart_refs(errors)
    check_staging_layout(errors)

    if errors:
        print("Layer contract checks failed:")
        for err in errors:
            print(f" - {err}")
        return 1

    print("Layer contract checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
