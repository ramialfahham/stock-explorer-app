"""Shared by the doc checks: the files under a repo root that match a set of glob patterns."""

from __future__ import annotations

from pathlib import Path


def files_matching(root: Path, patterns: tuple[str, ...]) -> set[str]:
    found: set[str] = set()
    for pattern in patterns:
        for p in root.glob(pattern):
            if p.is_file():
                found.add(p.relative_to(root).as_posix())
    return found
