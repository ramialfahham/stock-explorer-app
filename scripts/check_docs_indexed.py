"""Fail when a `docs/*.md` or `docs/ui/*.md` file has no markdown link pointing to it anywhere
in `CLAUDE.md` -- the file that calls itself "the map... which file owns what." Mirrors
`check_context_budget.py`'s "governed file with no entry" pattern, for discoverability instead
of size.

A link is any markdown `[text](path)` whose path resolves to the doc, with or without a
leading `./`, a `#fragment`, or the `docs/` prefix repeated relative to CLAUDE.md's own
location at the repo root.

Usage (from repo root):
    python scripts/check_docs_indexed.py
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
CLAUDE_MD = REPO_ROOT / "CLAUDE.md"
GOVERNED_GLOBS = ("docs/*.md", "docs/ui/*.md")

LINK_RE = re.compile(r"\]\(([^)]+)\)")


def governed_docs(root: Path) -> set[str]:
    found: set[str] = set()
    for pattern in GOVERNED_GLOBS:
        for p in root.glob(pattern):
            if p.is_file():
                found.add(p.relative_to(root).as_posix())
    return found


def linked_docs(claude_md: Path) -> set[str]:
    text = claude_md.read_text(encoding="utf-8")
    linked: set[str] = set()
    for match in LINK_RE.finditer(text):
        target = match.group(1).split("#", 1)[0].strip()
        target = target.removeprefix("./")
        if target.startswith("docs/"):
            linked.add(target)
    return linked


def find_violations(root: Path, claude_md: Path) -> list[str]:
    if not claude_md.is_file():
        return [f"{claude_md.name} does not exist"]
    governed = governed_docs(root)
    linked = linked_docs(claude_md)
    missing = sorted(governed - linked)
    return [f"{rel}: not linked from {claude_md.name}" for rel in missing]


def main() -> int:
    violations = find_violations(REPO_ROOT, CLAUDE_MD)
    if violations:
        print("Doc-index check FAILED:")
        for line in violations:
            print(f"  {line}")
        print("\nAdd a one-line [description](docs/the_file.md) entry for each to CLAUDE.md's "
              "\"Project knowledge\" section, or delete the file if it no longer belongs in "
              "the repo.")
        return 1
    print("Doc-index check passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
