from __future__ import annotations

from pathlib import Path

from governed_files import files_matching


def _touch(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("x", encoding="utf-8")


def test_matches_files_of_every_pattern_as_posix_paths(tmp_path: Path) -> None:
    _touch(tmp_path / "docs" / "a.md")
    _touch(tmp_path / "docs" / "ui" / "b.md")
    _touch(tmp_path / "docs" / "ui" / "deep" / "c.md")
    _touch(tmp_path / "other.md")

    assert files_matching(tmp_path, ("docs/*.md", "docs/ui/*.md")) == {"docs/a.md", "docs/ui/b.md"}


def test_a_directory_that_matches_a_pattern_is_not_a_file(tmp_path: Path) -> None:
    (tmp_path / "docs" / "folder.md").mkdir(parents=True)

    assert files_matching(tmp_path, ("docs/*.md",)) == set()
