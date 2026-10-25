"""Run the pinned official gitleaks release on the staged change (the pre-commit `gitleaks` hook).

pre-commit's own gitleaks hook compiles the tool from source into an unsigned .exe, which Windows
Smart App Control refuses (WinError 4551). The official release is run instead: downloaded once into
.cache/gitleaks/<version>/, checked against the SHA-256 pinned here, and started from Python like
every other hook in this repo. The full-history scan stays in CI (validate:secret-scan).
"""

from __future__ import annotations

import hashlib
import io
import os
import platform
import subprocess
import sys
import tarfile
import urllib.request
import zipfile
from collections.abc import Callable
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
VERSION = "8.30.1"
RELEASE_URL = "https://github.com/gitleaks/gitleaks/releases/download/v{version}/{asset}"
CACHE_DIR = REPO_ROOT / ".cache" / "gitleaks" / VERSION
CONFIG_PATH = REPO_ROOT / ".gitleaks.toml"

# (system, architecture) -> (release file, SHA-256 from the release's checksum file).
ASSETS: dict[tuple[str, str], tuple[str, str]] = {
    ("windows", "x64"): (
        "gitleaks_8.30.1_windows_x64.zip",
        "d29144deff3a68aa93ced33dddf84b7fdc26070add4aa0f4513094c8332afc4e",
    ),
    ("windows", "arm64"): (
        "gitleaks_8.30.1_windows_arm64.zip",
        "b95f5e4f5c425cedca7ee203d9afd29597e692c4924a12ed42f970537c72cc0f",
    ),
    ("linux", "x64"): (
        "gitleaks_8.30.1_linux_x64.tar.gz",
        "551f6fc83ea457d62a0d98237cbad105af8d557003051f41f3e7ca7b3f2470eb",
    ),
    ("linux", "arm64"): (
        "gitleaks_8.30.1_linux_arm64.tar.gz",
        "e4a487ee7ccd7d3a7f7ec08657610aa3606637dab924210b3aee62570fb4b080",
    ),
    ("darwin", "x64"): (
        "gitleaks_8.30.1_darwin_x64.tar.gz",
        "dfe101a4db2255fc85120ac7f3d25e4342c3c20cf749f2c20a18081af1952709",
    ),
    ("darwin", "arm64"): (
        "gitleaks_8.30.1_darwin_arm64.tar.gz",
        "b40ab0ae55c505963e365f271a8d3846efbc170aa17f2607f13df610a9aeb6a5",
    ),
}
_ARCHITECTURES = {"amd64": "x64", "x86_64": "x64", "arm64": "arm64", "aarch64": "arm64"}


class GitleaksError(Exception):
    """The scan could not run; the hook fails closed."""


def current_platform() -> tuple[str, str]:
    return platform.system().lower(), _ARCHITECTURES.get(platform.machine().lower(), platform.machine().lower())


def binary_name(system: str) -> str:
    return "gitleaks.exe" if system == "windows" else "gitleaks"


def asset_for(system: str, architecture: str) -> tuple[str, str]:
    try:
        return ASSETS[(system, architecture)]
    except KeyError:
        raise GitleaksError(
            f"no pinned gitleaks {VERSION} release for {system}/{architecture}; "
            "add its asset and SHA-256 to ASSETS in scripts/run_gitleaks.py"
        ) from None


def verify_sha256(data: bytes, expected: str, asset: str) -> None:
    actual = hashlib.sha256(data).hexdigest()
    if actual != expected:
        raise GitleaksError(f"{asset}: SHA-256 {actual} does not match the pinned {expected}; not used")


def extract_binary(asset: str, data: bytes, destination: Path) -> None:
    """Write only the gitleaks binary from the archive to `destination`, through a temp name."""
    wanted = destination.name
    if asset.endswith(".zip"):
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            content = archive.read(wanted)
    else:
        with tarfile.open(fileobj=io.BytesIO(data), mode="r:gz") as archive:
            member = archive.extractfile(wanted)
            if member is None:
                raise GitleaksError(f"{asset} has no {wanted}")
            content = member.read()
    destination.parent.mkdir(parents=True, exist_ok=True)
    partial = destination.with_name(f"{destination.name}.part-{os.getpid()}")
    try:
        partial.write_bytes(content)
        partial.chmod(0o755)
        os.replace(partial, destination)
    except BaseException:
        partial.unlink(missing_ok=True)
        raise


def _download(url: str) -> bytes:
    with urllib.request.urlopen(url, timeout=120) as response:
        return response.read()


def ensure_binary(
    system: str,
    architecture: str,
    *,
    cache_dir: Path = CACHE_DIR,
    fetch: Callable[[str], bytes] = _download,
) -> Path:
    binary = cache_dir / binary_name(system)
    if binary.exists():
        return binary
    asset, expected = asset_for(system, architecture)
    print(f"run_gitleaks: downloading gitleaks {VERSION} ({asset}) once into {cache_dir}", file=sys.stderr)
    try:
        data = fetch(RELEASE_URL.format(version=VERSION, asset=asset))
    except OSError as exc:
        raise GitleaksError(f"could not download {asset}: {exc}") from exc
    verify_sha256(data, expected, asset)
    extract_binary(asset, data, binary)
    return binary


def main() -> int:
    system, architecture = current_platform()
    try:
        binary = ensure_binary(system, architecture)
    except (GitleaksError, KeyError, zipfile.BadZipFile, tarfile.TarError) as exc:
        print(f"run_gitleaks: {exc}", file=sys.stderr)
        return 1
    command = [str(binary), "git", "--pre-commit", "--redact", "--staged", "--verbose", "--config", str(CONFIG_PATH)]
    return subprocess.run(command, cwd=REPO_ROOT).returncode


if __name__ == "__main__":
    sys.exit(main())
