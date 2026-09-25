"""Set up a fresh clone of this repo with one command, and prove it works with a second.

    python scripts/bootstrap.py            # set up everything that needs no credentials
    python scripts/bootstrap.py --verify   # tests, pre-commit on all files, sqlfluff, dbt build

A second run changes nothing: the file and remote steps skip, the installs repeat idempotently,
and no existing local file is overwritten.
Credentials are never read or written here: paste them into .env (see README "Getting started").
Standard library only: it runs before any dependency is installed.
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PYTHON_VERSION = (3, 11)
REQUIREMENTS = "requirements-dev.txt"
LOCAL_COPIES = ((".env.example", ".env"), ("profiles.yml.example", "profiles.yml"))
DBT = ["--project-dir", "dbt_analytics"]

# The deepest file an install writes is 165 characters below the repo root
# (.venv\Lib\site-packages\streamlit\.agents\skills\...\streamlit_app.cpython-311.pyc). Windows
# refuses paths over 259 characters unless long paths are enabled, so 80 leaves room to grow.
MAX_ROOT_CHARS_WITHOUT_LONG_PATHS = 80


class SetupError(Exception):
    pass


def say(status: str, message: str) -> None:
    print(f"[{status}] {message}", flush=True)


def run(cmd: list[str], cwd: Path = ROOT, env: dict[str, str] | None = None) -> None:
    say("run", " ".join(cmd))
    result = subprocess.run(cmd, cwd=cwd, env=env)
    if result.returncode != 0:
        raise SetupError(f"`{' '.join(cmd)}` failed with exit code {result.returncode}")


def tool(name: str) -> str:
    found = shutil.which(name)
    if not found:
        raise SetupError(f"`{name}` is not installed or not on PATH. See README 'Getting started'.")
    return found


def venv_tool(name: str, root: Path = ROOT) -> Path:
    if os.name == "nt":
        return root / ".venv" / "Scripts" / f"{name}.exe"
    return root / ".venv" / "bin" / name


def venv_python(root: Path = ROOT) -> Path:
    return venv_tool("python", root)


def path_too_long(root: Path, is_windows: bool, long_paths_enabled: bool) -> bool:
    return is_windows and not long_paths_enabled and len(str(root)) > MAX_ROOT_CHARS_WITHOUT_LONG_PATHS


def windows_long_paths_enabled() -> bool:
    import winreg

    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Control\FileSystem") as key:
            return winreg.QueryValueEx(key, "LongPathsEnabled")[0] == 1
    except OSError:
        return False


def remote_rename_needed(remotes: dict[str, str]) -> bool:
    return "gitlab" not in remotes and "gitlab.com" in remotes.get("origin", "")


def copy_if_missing(source: Path, target: Path) -> bool:
    if target.exists():
        return False
    shutil.copyfile(source, target)
    return True


def check_prerequisites() -> None:
    if sys.version_info[:2] != PYTHON_VERSION:
        raise SetupError(
            f"Run this with Python {PYTHON_VERSION[0]}.{PYTHON_VERSION[1]} (found "
            f"{sys.version_info[0]}.{sys.version_info[1]}). On Windows: py -3.11 scripts/bootstrap.py"
        )
    if os.name == "nt" and path_too_long(ROOT, True, windows_long_paths_enabled()):
        raise SetupError(
            f"The repo folder path is {len(str(ROOT))} characters long and Windows long paths are off, "
            "so the install would fail with 'file name too long'. Clone into a short folder "
            r"(for example C:\src\stock-explorer-app), or turn on long paths as described in the README."
        )
    tool("git")


def check_hooks_path() -> None:
    result = subprocess.run(
        ["git", "config", "--get", "core.hooksPath"], cwd=ROOT, capture_output=True, text=True
    )
    if result.stdout.strip():
        raise SetupError(
            "git's core.hooksPath is set, so pre-commit cannot install its hooks. "
            "Remove it with: git config --unset-all core.hooksPath (then run this again)."
        )


def set_up_remote() -> None:
    if os.environ.get("CI"):
        # CI checks (scripts/check_no_em_dash.py) fetch the MR base from `origin`.
        say("skip", "git remote: CI clone keeps origin")
        return
    names = subprocess.run(["git", "remote"], cwd=ROOT, capture_output=True, text=True).stdout.split()
    remotes = {
        name: subprocess.run(
            ["git", "remote", "get-url", name], cwd=ROOT, capture_output=True, text=True
        ).stdout.strip()
        for name in names
    }
    if remote_rename_needed(remotes):
        run(["git", "remote", "rename", "origin", "gitlab"])
    else:
        say("skip", "git remote: nothing to rename")


def set_up_python() -> Path:
    python = venv_python()
    if python.exists():
        say("skip", ".venv exists")
    else:
        run([sys.executable, "-m", "venv", ".venv"])
    version = subprocess.run(
        [str(python), "-c", "import sys; print(sys.version_info[0], sys.version_info[1])"],
        capture_output=True,
        text=True,
    ).stdout.split()
    if tuple(int(part) for part in version) != PYTHON_VERSION:
        raise SetupError(
            f".venv uses Python {'.'.join(version)}, not {PYTHON_VERSION[0]}.{PYTHON_VERSION[1]}. "
            "Delete .venv and run this again."
        )
    run([str(python), "-m", "pip", "install", "--quiet", "--upgrade", "pip"])
    run([str(python), "-m", "pip", "install", "--quiet", "-r", REQUIREMENTS])
    return python


def set_up_local_files() -> None:
    for source, target in LOCAL_COPIES:
        if copy_if_missing(ROOT / source, ROOT / target):
            say("ok", f"created {target} from {source}")
        else:
            say("skip", f"{target} exists, left unchanged")


def set_up(python: Path) -> None:
    run([str(python), "-m", "pre_commit", "install", "--install-hooks"])
    run([str(venv_tool("dbt")), "deps", *DBT, "--profiles-dir", ".", "--quiet"])


def verify_env(work: Path) -> dict[str, str]:
    """The environment for the proof's dbt build: fixtures and the DuckDB file live in `work`,
    never in storage/raw (real ingested data) or the home folder."""
    return {**os.environ, "DBT_RAW_PATH": (work / "raw").as_posix()}


def verify(python: Path) -> None:
    run([str(python), "-m", "pytest", "tests", "-q", "--no-header"])
    run(
        [str(python), "-m", "pre_commit", "run", "--all-files", "--show-diff-on-failure"],
        env={**os.environ, "SKIP": "no-commit-to-branch"},
    )
    run([str(venv_tool("sqlfluff")), "lint", "dbt_analytics/models", "dbt_analytics/tests"])
    with tempfile.TemporaryDirectory(prefix="stock-explorer-verify-", ignore_cleanup_errors=True) as tmp:
        work = Path(tmp)
        run([str(python), "scripts/write_ci_dbt_profile.py",
             "--path", (work / "verify.db").as_posix(), "--profiles-dir", str(work)])
        run([str(python), "scripts/seed_ci_raw_fixtures.py", "--out-dir", str(work / "raw")])
        run([str(venv_tool("dbt")), "build", *DBT, "--profiles-dir", str(work)], env=verify_env(work))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--verify", action="store_true", help="prove the setup works (no credentials)")
    args = parser.parse_args(argv)
    try:
        if args.verify:
            python = venv_python()
            if not python.exists():
                raise SetupError("no .venv yet: run `python scripts/bootstrap.py` first")
            verify(python)
            say("ok", "verified: tests, pre-commit, sqlfluff and the dbt build pass")
            return 0
        check_prerequisites()
        check_hooks_path()
        set_up_remote()
        python = set_up_python()
        set_up_local_files()
        set_up(python)
        say("ok", "setup complete. Prove it with: python scripts/bootstrap.py --verify")
        return 0
    except SetupError as error:
        say("stop", str(error))
        return 1


if __name__ == "__main__":
    sys.exit(main())
