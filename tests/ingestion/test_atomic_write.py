"""replace_atomically: a file is the last complete write or the new one, never a partial one."""

from __future__ import annotations

from pathlib import Path

import pytest

from ingestion.atomic_write import replace_atomically


def test_the_target_is_replaced_and_no_temp_file_is_left(tmp_path: Path) -> None:
    target = tmp_path / "nested" / "file.txt"
    replace_atomically(target, lambda tmp: tmp.write_text("first", encoding="utf-8"))
    replace_atomically(target, lambda tmp: tmp.write_text("second", encoding="utf-8"))

    assert target.read_text(encoding="utf-8") == "second"
    assert list(target.parent.iterdir()) == [target]


def test_a_write_that_raises_leaves_the_previous_file_and_no_temp_file(tmp_path: Path) -> None:
    target = tmp_path / "file.txt"
    replace_atomically(target, lambda tmp: tmp.write_text("complete", encoding="utf-8"))

    def failing_write(tmp: Path) -> None:
        tmp.write_text("trunc", encoding="utf-8")
        raise OSError("disk full")

    with pytest.raises(OSError, match="disk full"):
        replace_atomically(target, failing_write)

    assert target.read_text(encoding="utf-8") == "complete"
    assert list(tmp_path.iterdir()) == [target]


def test_a_first_write_that_raises_creates_no_target(tmp_path: Path) -> None:
    target = tmp_path / "file.txt"

    def failing_write(tmp: Path) -> None:
        tmp.write_text("trunc", encoding="utf-8")
        raise KeyboardInterrupt

    with pytest.raises(KeyboardInterrupt):
        replace_atomically(target, failing_write)

    assert list(tmp_path.iterdir()) == []
