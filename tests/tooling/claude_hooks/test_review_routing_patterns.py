"""Every pattern in review_routing.json matches at least one tracked file, so no route is
silently dead. Matching is the review gate's own: fnmatch against repo-relative paths."""

from __future__ import annotations

import fnmatch
import json
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
ROUTING = json.loads((ROOT / ".claude" / "review_routing.json").read_text(encoding="utf-8"))
PATTERNS = sorted(
    {*ROUTING["paths"], *ROUTING["artifact_only"], *ROUTING["artifact_only_never"]}
)


@pytest.fixture(scope="module")
def tracked() -> list[str]:
    files = subprocess.run(
        ["git", "ls-files"], cwd=ROOT, capture_output=True, text=True, check=True
    ).stdout.splitlines()
    assert files
    return files


@pytest.mark.parametrize("pattern", PATTERNS)
def test_routing_pattern_matches_a_tracked_file(pattern: str, tracked: list[str]) -> None:
    assert any(fnmatch.fnmatch(path, pattern) for path in tracked), (
        f"{pattern} matches no tracked file; remove it from review_routing.json"
    )
