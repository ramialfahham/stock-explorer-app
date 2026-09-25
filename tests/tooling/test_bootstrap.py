"""Pin what `scripts/bootstrap.py` decides: skip what is done, never overwrite, never print a
remote URL, and never point the proof's dbt build at real data."""

from __future__ import annotations

from pathlib import Path

import pytest

import bootstrap

TOKEN_URL = "https://gitlab-ci-token:s3cret-token-0123456789@gitlab.com/group/repo.git"


def test_copy_if_missing_creates_the_file(tmp_path: Path) -> None:
    source, target = tmp_path / "a.example", tmp_path / "a"
    source.write_text("template", encoding="utf-8")

    assert bootstrap.copy_if_missing(source, target) is True
    assert target.read_text(encoding="utf-8") == "template"


def test_copy_if_missing_never_overwrites(tmp_path: Path) -> None:
    source, target = tmp_path / "a.example", tmp_path / "a"
    source.write_text("template", encoding="utf-8")
    target.write_text("mine", encoding="utf-8")

    assert bootstrap.copy_if_missing(source, target) is False
    assert target.read_text(encoding="utf-8") == "mine"


def test_local_files_second_run_skips_and_keeps_edits(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    for source, _ in bootstrap.LOCAL_COPIES:
        (tmp_path / source).write_text("template", encoding="utf-8")
    monkeypatch.setattr(bootstrap, "ROOT", tmp_path)

    bootstrap.set_up_local_files()
    for _, target in bootstrap.LOCAL_COPIES:
        (tmp_path / target).write_text("edited", encoding="utf-8")
    capsys.readouterr()
    bootstrap.set_up_local_files()

    out = capsys.readouterr().out
    assert "[ok]" not in out and out.count("[skip]") == len(bootstrap.LOCAL_COPIES)
    for _, target in bootstrap.LOCAL_COPIES:
        assert (tmp_path / target).read_text(encoding="utf-8") == "edited"


@pytest.mark.parametrize(
    ("root", "is_windows", "long_paths", "expected"),
    [
        ("C:\\" + "x" * 90, True, False, True),
        ("C:\\" + "x" * 90, True, True, False),
        ("C:\\" + "x" * 90, False, False, False),
        ("C:\\01_Projects\\stock-explorer-app", True, False, False),
    ],
)
def test_path_too_long_only_when_windows_limits_apply(root, is_windows, long_paths, expected) -> None:
    assert bootstrap.path_too_long(Path(root), is_windows, long_paths) is expected


@pytest.mark.parametrize(
    ("remotes", "expected"),
    [
        ({"origin": "https://gitlab.com/group/repo.git"}, True),
        ({"origin": "https://github.com/owner/repo.git"}, False),
        ({"gitlab": "https://gitlab.com/group/repo.git"}, False),
        ({"origin": "https://gitlab.com/a.git", "gitlab": "https://gitlab.com/b.git"}, False),
        ({}, False),
    ],
)
def test_remote_is_renamed_only_for_a_gitlab_origin_without_a_gitlab_remote(remotes, expected) -> None:
    assert bootstrap.remote_rename_needed(remotes) is expected


def test_set_up_remote_never_prints_the_remote_url(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    # CI clones carry a job token in origin's URL; it must not reach the job log.
    class Result:
        def __init__(self, stdout: str) -> None:
            self.stdout, self.returncode = stdout, 0

    def fake_run(cmd, **kwargs):
        if cmd[:2] == ["git", "remote"] and len(cmd) == 2:
            return Result("origin\n")
        if cmd[:3] == ["git", "remote", "get-url"]:
            return Result(TOKEN_URL + "\n")
        return Result("")

    monkeypatch.setattr(bootstrap.subprocess, "run", fake_run)
    monkeypatch.delenv("CI", raising=False)

    bootstrap.set_up_remote()

    output = capsys.readouterr()
    assert "rename origin gitlab" in output.out
    assert "s3cret-token" not in output.out and "s3cret-token" not in output.err


def test_ci_clone_keeps_origin(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[list[str]] = []
    monkeypatch.setenv("CI", "true")
    monkeypatch.setattr(bootstrap.subprocess, "run", lambda cmd, **kwargs: calls.append(cmd))
    monkeypatch.setattr(bootstrap, "run", lambda cmd, **kwargs: calls.append(cmd))

    bootstrap.set_up_remote()

    assert calls == []


def test_verify_never_points_the_dbt_build_at_storage_raw(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[list[str], dict[str, str] | None]] = []
    monkeypatch.setattr(bootstrap, "run", lambda cmd, cwd=bootstrap.ROOT, env=None: calls.append((cmd, env)))

    bootstrap.verify(Path("python"))

    seed = next(cmd for cmd, _ in calls if "scripts/seed_ci_raw_fixtures.py" in cmd)
    out_dir = Path(seed[seed.index("--out-dir") + 1])
    build_cmd, build_env = next((cmd, env) for cmd, env in calls if "build" in cmd)
    profiles_dir = Path(build_cmd[build_cmd.index("--profiles-dir") + 1])

    raw = bootstrap.ROOT / "storage" / "raw"
    assert out_dir.parent == profiles_dir
    assert Path(build_env["DBT_RAW_PATH"]) == out_dir
    for path in (out_dir, profiles_dir):
        assert raw not in path.parents and path != raw
        assert bootstrap.ROOT not in path.parents
        assert Path.home() / ".dbt" != path


def test_verify_skips_only_the_branch_guard(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[list[str], dict[str, str] | None]] = []
    monkeypatch.setattr(bootstrap, "run", lambda cmd, cwd=bootstrap.ROOT, env=None: calls.append((cmd, env)))

    bootstrap.verify(Path("python"))

    env = next(env for cmd, env in calls if "pre_commit" in cmd)
    assert env["SKIP"] == "no-commit-to-branch"
