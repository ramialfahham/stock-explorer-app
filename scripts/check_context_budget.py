"""Fail when a context file exceeds its byte budget, or exists without one.

Budgets: docs/context_budget.yml. Governed files: every Markdown file matching GOVERNED_GLOBS.
Three failures, each printed as one line with the path, the size and the budget:
over budget, governed but unbudgeted, budgeted but missing.

Size is measured with CRLF collapsed to LF, so a Windows checkout (core.autocrlf=true) and the
Linux CI runner agree on the number.

Usage (from repo root):
    python scripts/check_context_budget.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
BUDGET_PATH = REPO_ROOT / "docs" / "context_budget.yml"
GOVERNED_GLOBS = ("CLAUDE.md", ".claude/*.md", ".claude/task/*.md", "docs/*.md", "docs/ui/*.md")


def load_budgets(path: Path) -> dict[str, int]:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    budgets = data.get("budgets") or {}
    out: dict[str, int] = {}
    for rel, limit in budgets.items():
        if not isinstance(limit, int) or isinstance(limit, bool) or limit <= 0:
            raise ValueError(
                f"{path.name}: budget for {rel} must be a positive integer, got {limit!r}"
            )
        out[str(rel)] = limit
    return out


def measured_size(path: Path) -> int:
    return len(path.read_bytes().replace(b"\r\n", b"\n"))


def governed_files(root: Path) -> set[str]:
    found: set[str] = set()
    for pattern in GOVERNED_GLOBS:
        for p in root.glob(pattern):
            if p.is_file():
                found.add(p.relative_to(root).as_posix())
    return found


def find_violations(root: Path, budgets: dict[str, int]) -> list[str]:
    violations: list[str] = []
    governed = governed_files(root)
    for rel in sorted(governed - set(budgets)):
        size = measured_size(root / rel)
        violations.append(f"{rel}: {size} bytes, no budget in {BUDGET_PATH.name}")
    for rel in sorted(budgets):
        path = root / rel
        if not path.is_file():
            violations.append(
                f"{rel}: budgeted at {budgets[rel]} bytes but the file does not exist"
            )
            continue
        size = measured_size(path)
        if size > budgets[rel]:
            violations.append(
                f"{rel}: {size} bytes, budget {budgets[rel]}, over by {size - budgets[rel]}"
            )
    return violations


def main() -> int:
    budgets = load_budgets(BUDGET_PATH)
    violations = find_violations(REPO_ROOT, budgets)
    if violations:
        print("Context budget check FAILED:")
        for line in violations:
            print(f"  {line}")
        return 1
    print(f"Context budget check passed ({len(budgets)} files).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
