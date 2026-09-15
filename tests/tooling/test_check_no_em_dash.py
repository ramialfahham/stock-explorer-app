"""This is a guard, so each test proves it fires, not that a happy path passes. Diff parsing
(hunk headers, +/-/context line tracking) is the risky part -- covered directly here rather
than trusting `git diff`'s format by inspection alone."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from check_no_em_dash import _ALL_ZERO_SHA, _get_diff, find_violations, main  # noqa: E402


def _diff(*lines: str) -> bytes:
    return ("\n".join(lines) + "\n").encode("utf-8")


def _git(args: list[str], cwd: Path) -> str:
    result = subprocess.run(
        ["git", *args], cwd=cwd, capture_output=True, text=True, timeout=30,
    )
    assert result.returncode == 0, result.stderr
    return result.stdout.strip()


def _init_repo(root: Path) -> None:
    _git(["init", "-q", "-b", "main"], root)
    _git(["-c", "user.email=t@t.com", "-c", "user.name=t", "commit", "-q", "--allow-empty",
          "-m", "init"], root)


def test_an_em_dash_on_an_added_line_fails() -> None:
    diff = _diff(
        "diff --git a/f.txt b/f.txt",
        "--- a/f.txt",
        "+++ b/f.txt",
        "@@ -1,1 +1,1 @@",
        "-old",
        f"+new{chr(0x2014)}dash",
    )
    violations = find_violations(diff)
    assert len(violations) == 1
    assert "f.txt:1" in violations[0]


def test_an_en_dash_on_an_added_line_fails() -> None:
    diff = _diff(
        "diff --git a/f.txt b/f.txt",
        "--- a/f.txt",
        "+++ b/f.txt",
        "@@ -1,1 +1,1 @@",
        "-old",
        f"+new{chr(0x2013)}dash",
    )
    violations = find_violations(diff)
    assert len(violations) == 1


def test_a_double_hyphen_on_an_added_line_passes() -> None:
    diff = _diff(
        "diff --git a/f.txt b/f.txt",
        "--- a/f.txt",
        "+++ b/f.txt",
        "@@ -1,1 +1,1 @@",
        "-old",
        "+new -- dash",
    )
    assert find_violations(diff) == []


def test_a_pre_existing_em_dash_on_an_untouched_context_line_passes() -> None:
    diff = _diff(
        "diff --git a/f.txt b/f.txt",
        "--- a/f.txt",
        "+++ b/f.txt",
        "@@ -1,3 +1,3 @@",
        " line1",
        f" line2 with {chr(0x2014)} unchanged",
        "-line3 old",
        "+line3 new",
    )
    assert find_violations(diff) == []


def test_the_correct_new_file_line_number_is_reported_past_the_first_hunk() -> None:
    diff = _diff(
        "diff --git a/f.txt b/f.txt",
        "--- a/f.txt",
        "+++ b/f.txt",
        "@@ -1,2 +1,2 @@",
        " line1",
        "-line2 old",
        "+line2 new",
        "@@ -10,2 +10,3 @@",
        " line10",
        "+line11 new",
        f"+line12 new {chr(0x2014)} dash",
    )
    violations = find_violations(diff)
    assert len(violations) == 1
    assert "f.txt:12" in violations[0]


def test_a_deleted_line_with_an_em_dash_is_not_a_violation() -> None:
    diff = _diff(
        "diff --git a/f.txt b/f.txt",
        "--- a/f.txt",
        "+++ b/f.txt",
        "@@ -1,1 +1,1 @@",
        f"-old {chr(0x2014)} dash",
        "+new",
    )
    assert find_violations(diff) == []


def test_a_second_file_in_the_same_diff_tracks_its_own_line_numbers() -> None:
    diff = _diff(
        "diff --git a/a.txt b/a.txt",
        "--- a/a.txt",
        "+++ b/a.txt",
        "@@ -1,1 +1,1 @@",
        "-old",
        "+new a clean",
        "diff --git a/b.txt b/b.txt",
        "--- a/b.txt",
        "+++ b/b.txt",
        "@@ -1,1 +1,1 @@",
        "-old",
        f"+new b {chr(0x2013)} dash",
    )
    violations = find_violations(diff)
    assert len(violations) == 1
    assert "b.txt:1" in violations[0]


def test_an_empty_diff_has_no_violations() -> None:
    assert find_violations(b"") == []


def test_ci_uses_mr_target_branch_merge_base(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _init_repo(tmp_path)
    (tmp_path / "f.txt").write_text("line1\n", encoding="utf-8")
    _git(["add", "f.txt"], tmp_path)
    _git(["-c", "user.email=t@t.com", "-c", "user.name=t", "commit", "-q", "-m", "add f"], tmp_path)
    _git(["checkout", "-q", "-b", "feature"], tmp_path)
    (tmp_path / "f.txt").write_text(f"line1\nline2 {chr(0x2014)} dash\n", encoding="utf-8")
    _git(["add", "f.txt"], tmp_path)
    _git(["-c", "user.email=t@t.com", "-c", "user.name=t", "commit", "-q", "-m", "edit f"], tmp_path)
    # No real "origin" remote in this throwaway repo -- point it at itself so `git fetch
    # origin main` and `origin/main` resolve.
    _git(["remote", "add", "origin", str(tmp_path)], tmp_path)

    monkeypatch.setenv("CI", "true")
    monkeypatch.setenv("CI_MERGE_REQUEST_TARGET_BRANCH_NAME", "main")
    monkeypatch.delenv("CI_COMMIT_BEFORE_SHA", raising=False)

    diff, source = _get_diff(tmp_path)
    assert diff is not None
    assert "merge-base" in source
    violations = find_violations(diff)
    assert len(violations) == 1
    assert "f.txt:2" in violations[0]


def test_ci_falls_back_to_commit_before_sha_on_a_push_pipeline(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _init_repo(tmp_path)
    (tmp_path / "f.txt").write_text("line1\n", encoding="utf-8")
    _git(["add", "f.txt"], tmp_path)
    _git(["-c", "user.email=t@t.com", "-c", "user.name=t", "commit", "-q", "-m", "add f"], tmp_path)
    before_sha = _git(["rev-parse", "HEAD"], tmp_path)
    (tmp_path / "f.txt").write_text(f"line1\nline2 {chr(0x2013)} dash\n", encoding="utf-8")
    _git(["add", "f.txt"], tmp_path)
    _git(["-c", "user.email=t@t.com", "-c", "user.name=t", "commit", "-q", "-m", "edit f"], tmp_path)

    monkeypatch.setenv("CI", "true")
    monkeypatch.delenv("CI_MERGE_REQUEST_TARGET_BRANCH_NAME", raising=False)
    monkeypatch.setenv("CI_COMMIT_BEFORE_SHA", before_sha)

    diff, source = _get_diff(tmp_path)
    assert diff is not None
    assert "CI_COMMIT_BEFORE_SHA" in source
    violations = find_violations(diff)
    assert len(violations) == 1
    assert "f.txt:2" in violations[0]


def test_ci_treats_the_all_zero_before_sha_as_unavailable(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _init_repo(tmp_path)
    monkeypatch.setenv("CI", "true")
    monkeypatch.delenv("CI_MERGE_REQUEST_TARGET_BRANCH_NAME", raising=False)
    monkeypatch.setenv("CI_COMMIT_BEFORE_SHA", _ALL_ZERO_SHA)

    diff, source = _get_diff(tmp_path)
    assert diff is None
    assert "cannot determine" in source


def test_ci_with_no_usable_base_returns_none_with_a_diagnostic(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _init_repo(tmp_path)
    monkeypatch.setenv("CI", "true")
    monkeypatch.delenv("CI_MERGE_REQUEST_TARGET_BRANCH_NAME", raising=False)
    monkeypatch.delenv("CI_COMMIT_BEFORE_SHA", raising=False)

    diff, source = _get_diff(tmp_path)
    assert diff is None
    assert "cannot determine" in source


def test_main_fails_closed_in_ci_when_no_base_is_available(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import check_no_em_dash

    monkeypatch.setenv("CI", "true")
    monkeypatch.setattr(
        check_no_em_dash, "_get_diff", lambda root: (None, "CI: nothing usable")
    )
    assert main() == 1


def test_main_passes_locally_when_there_is_nothing_staged(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import check_no_em_dash

    monkeypatch.delenv("CI", raising=False)
    monkeypatch.setattr(
        check_no_em_dash, "_get_diff", lambda root: (None, "nothing staged")
    )
    assert main() == 0
