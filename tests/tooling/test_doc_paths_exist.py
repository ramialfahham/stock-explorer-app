"""A backticked repo path in a governed doc (the GOVERNED_MARKDOWN set) must exist, so a moved or
renamed file shows up as a failing test rather than a doc pointing at nothing. Every
whitespace-separated word inside a backtick span is checked, so a path inside a command
(`pytest tests/x.py`) counts. Only words with a directory part and a known text extension are
paths; a placeholder (`{market_code}`, `*`) cannot match that shape and is never checked."""

from __future__ import annotations

import posixpath
import re
from pathlib import Path

import pytest

from check_no_narrative_dates import EXCLUDE_DIR_PARTS, REPO_ROOT, is_governed_markdown

SPAN = re.compile(r"`([^`\n]+)`")
PATH_WORD = re.compile(
    r"[A-Za-z0-9_.\-/]+/[A-Za-z0-9_.\-]+\.(?:py|md|yml|yaml|sql|csv|json|toml|txt|js)"
)


def governed_docs(root: Path) -> list[Path]:
    return sorted(
        p for p in root.rglob("*.md")
        if not EXCLUDE_DIR_PARTS.intersection(p.relative_to(root).parts)
        and is_governed_markdown(p, root)
    )


def missing_paths(root: Path) -> list[str]:
    missing = []
    for doc in governed_docs(root):
        base = doc.relative_to(root).parent.as_posix()
        for lineno, line in enumerate(doc.read_text(encoding="utf-8").splitlines(), start=1):
            for span in SPAN.findall(line):
                for word in span.split():
                    if not PATH_WORD.fullmatch(word):
                        continue
                    candidates = {
                        posixpath.normpath(word), posixpath.normpath(posixpath.join(base, word))
                    }
                    if not any((root / c).is_file() for c in candidates):
                        missing.append(f"{doc.relative_to(root).as_posix()}:{lineno}: {word}")
    return missing


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


@pytest.mark.parametrize(
    "span", ["tests/test_gone.py", "pytest tests/test_gone.py", "python tests/test_gone.py --x"]
)
def test_a_missing_path_in_a_governed_doc_is_reported(tmp_path: Path, span: str) -> None:
    _write(tmp_path / "docs" / "a.md", f"Run `{span}` for the guard.\n")
    assert missing_paths(tmp_path) == ["docs/a.md:1: tests/test_gone.py"]


@pytest.mark.parametrize(
    "span",
    [
        "scripts/real.py",
        "../scripts/real.py",
        "python scripts/real.py --market x",
        "storage/seeds/{market_code}/x.csv",
        "docs/*.md",
    ],
)
def test_existing_relative_and_placeholder_paths_pass(tmp_path: Path, span: str) -> None:
    _write(tmp_path / "scripts" / "real.py", "")
    _write(tmp_path / "docs" / "a.md", f"See `{span}`.\n")
    assert missing_paths(tmp_path) == []


@pytest.mark.parametrize("rel", ["tests/README.md", ".venv/docs/a.md"])
def test_a_doc_outside_the_governed_set_is_not_checked(tmp_path: Path, rel: str) -> None:
    _write(tmp_path / rel, "See `tests/test_gone.py`.\n")
    assert missing_paths(tmp_path) == []


def test_every_path_a_governed_doc_names_exists() -> None:
    assert missing_paths(REPO_ROOT) == []
