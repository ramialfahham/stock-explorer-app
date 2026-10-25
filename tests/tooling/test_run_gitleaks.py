"""scripts/run_gitleaks.py: a downloaded release is checked against its pinned SHA-256 before it is
extracted, and the scan fails closed."""

from __future__ import annotations

import hashlib
import io
import re
import sys
import tarfile
import zipfile
from pathlib import Path

import pytest

import run_gitleaks as rg

CI_FILE = Path(__file__).resolve().parents[2] / ".gitlab-ci.yml"


def _zip(members: dict[str, bytes]) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        for name, content in members.items():
            archive.writestr(name, content)
    return buffer.getvalue()


def _targz(members: dict[str, bytes]) -> bytes:
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode="w:gz") as archive:
        for name, content in members.items():
            info = tarfile.TarInfo(name)
            info.size = len(content)
            archive.addfile(info, io.BytesIO(content))
    return buffer.getvalue()


def test_the_version_equals_the_ci_scan_image() -> None:
    match = re.search(r"zricethezav/gitleaks:v([0-9.]+)", CI_FILE.read_text(encoding="utf-8"))
    assert match and match.group(1) == rg.VERSION


def test_every_pinned_asset_names_the_pinned_version_and_a_sha256() -> None:
    for (system, architecture), (asset, digest) in rg.ASSETS.items():
        assert asset.startswith(f"gitleaks_{rg.VERSION}_{system}_{architecture}.")
        assert re.fullmatch(r"[0-9a-f]{64}", digest)


@pytest.mark.parametrize(
    ("system", "machine", "expected"),
    [
        ("Windows", "AMD64", ("windows", "x64")),
        ("Linux", "x86_64", ("linux", "x64")),
        ("Linux", "aarch64", ("linux", "arm64")),
        ("Darwin", "arm64", ("darwin", "arm64")),
    ],
)
def test_the_platform_is_normalised_to_the_release_names(monkeypatch, system, machine, expected) -> None:
    monkeypatch.setattr(rg.platform, "system", lambda: system)
    monkeypatch.setattr(rg.platform, "machine", lambda: machine)
    assert rg.current_platform() == expected


@pytest.mark.parametrize(
    ("system", "asset", "build", "member"),
    [
        ("windows", f"gitleaks_{rg.VERSION}_windows_x64.zip", _zip, "gitleaks.exe"),
        ("linux", f"gitleaks_{rg.VERSION}_linux_x64.tar.gz", _targz, "gitleaks"),
    ],
)
def test_a_download_that_matches_the_pinned_hash_is_extracted_alone(
    monkeypatch, tmp_path: Path, system, asset, build, member
) -> None:
    data = build({member: b"the binary", "README.md": b"docs", "../escape": b"x"})
    architecture = "x64"
    monkeypatch.setitem(rg.ASSETS, (system, architecture), (asset, hashlib.sha256(data).hexdigest()))
    requested: list[str] = []

    def fetch(url: str) -> bytes:
        requested.append(url)
        return data

    cache = tmp_path / "cache"
    binary = rg.ensure_binary(system, architecture, cache_dir=cache, fetch=fetch)

    assert binary == cache / member
    assert binary.read_bytes() == b"the binary"
    assert sorted(p.name for p in cache.iterdir()) == [member]
    assert requested == [f"https://github.com/gitleaks/gitleaks/releases/download/v{rg.VERSION}/{asset}"]


def test_a_download_with_the_wrong_hash_is_refused_and_leaves_nothing(tmp_path: Path) -> None:
    cache = tmp_path / "cache"
    with pytest.raises(rg.GitleaksError, match="does not match the pinned"):
        rg.ensure_binary("windows", "x64", cache_dir=cache, fetch=lambda url: _zip({"gitleaks.exe": b"tampered"}))

    assert not cache.exists() or list(cache.iterdir()) == []


def test_the_cached_binary_is_reused_without_a_download(tmp_path: Path) -> None:
    cache = tmp_path / "cache"
    cache.mkdir()
    (cache / "gitleaks.exe").write_bytes(b"cached")

    def fetch(url: str) -> bytes:
        raise AssertionError("must not download when the binary is cached")

    assert rg.ensure_binary("windows", "x64", cache_dir=cache, fetch=fetch) == cache / "gitleaks.exe"


def test_a_failed_download_is_reported_not_raised_as_an_os_error(tmp_path: Path) -> None:
    def fetch(url: str) -> bytes:
        raise OSError("no network")

    with pytest.raises(rg.GitleaksError, match="could not download .*no network"):
        rg.ensure_binary("windows", "x64", cache_dir=tmp_path / "cache", fetch=fetch)


def test_an_unsupported_platform_is_refused() -> None:
    with pytest.raises(rg.GitleaksError, match="no pinned gitleaks .* plan9/x64"):
        rg.asset_for("plan9", "x64")


def test_main_runs_the_scan_on_the_staged_change_with_the_repo_config(monkeypatch) -> None:
    calls: list[tuple[list[str], Path]] = []

    class _Result:
        returncode = 7

    def fake_run(command, cwd=None, **kwargs):
        calls.append((command, cwd))
        return _Result()

    monkeypatch.setattr(rg, "current_platform", lambda: ("linux", "x64"))
    monkeypatch.setattr(rg, "ensure_binary", lambda system, architecture: Path("/cache/gitleaks"))
    monkeypatch.setattr(rg.subprocess, "run", fake_run)

    assert rg.main() == 7

    command, cwd = calls[0]
    assert command[1:] == ["git", "--pre-commit", "--redact", "--staged", "--verbose", "--config", str(rg.CONFIG_PATH)]
    assert cwd == rg.REPO_ROOT


def test_main_fails_closed_when_the_scanner_cannot_be_obtained(monkeypatch, capsys) -> None:
    def broken(system, architecture):
        raise rg.GitleaksError("could not download x: no network")

    monkeypatch.setattr(rg, "current_platform", lambda: ("linux", "x64"))
    monkeypatch.setattr(rg, "ensure_binary", broken)
    monkeypatch.setattr(rg.subprocess, "run", lambda *a, **k: pytest.fail("the scan must not run"))

    assert rg.main() == 1
    assert "could not download x" in capsys.readouterr().err


def test_a_failed_move_into_place_leaves_no_partial_file(monkeypatch, tmp_path: Path) -> None:
    def failing_replace(source, destination):
        raise OSError("disk full")

    monkeypatch.setattr(rg.os, "replace", failing_replace)
    destination = tmp_path / "cache" / "gitleaks.exe"

    with pytest.raises(OSError, match="disk full"):
        rg.extract_binary(f"gitleaks_{rg.VERSION}_windows_x64.zip", _zip({"gitleaks.exe": b"binary"}), destination)

    assert list(destination.parent.iterdir()) == []


def test_main_fails_closed_when_the_binary_cannot_be_unpacked(monkeypatch, capsys) -> None:
    def missing_member(system, architecture):
        raise KeyError("gitleaks.exe")

    monkeypatch.setattr(rg, "current_platform", lambda: ("windows", "x64"))
    monkeypatch.setattr(rg, "ensure_binary", missing_member)
    monkeypatch.setattr(rg.subprocess, "run", lambda *a, **k: pytest.fail("the scan must not run"))

    assert rg.main() == 1
    assert "gitleaks.exe" in capsys.readouterr().err


@pytest.mark.skipif(sys.platform == "win32", reason="Windows has no executable bit")
def test_the_extracted_binary_is_executable(tmp_path: Path) -> None:
    destination = tmp_path / "cache" / "gitleaks"
    rg.extract_binary("gitleaks_x_linux_x64.tar.gz", _targz({"gitleaks": b"binary"}), destination)

    assert destination.stat().st_mode & 0o111 == 0o111


@pytest.mark.parametrize(
    ("asset", "build", "name"),
    [("x.zip", _zip, "gitleaks.exe"), ("x.tar.gz", _targz, "gitleaks")],
)
def test_an_archive_without_the_binary_is_refused(tmp_path: Path, asset, build, name) -> None:
    destination = tmp_path / "cache" / name

    with pytest.raises(KeyError):
        rg.extract_binary(asset, build({"README.md": b"docs"}), destination)

    assert not destination.parent.exists() or list(destination.parent.iterdir()) == []
