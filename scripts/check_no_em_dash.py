"""Fail when an added or edited line carries an em-dash (U+2014) or en-dash (U+2013), per
engineering_standards.md §1.3: "No em-dash or en-dash on any line you add or edit, in any
file. Use `--`." A pre-existing dash on an untouched line is not a violation -- this checks a
diff, not the whole tree, unlike check_context_budget.py and check_no_narrative_dates.py.

Diff source:
  - Locally (pre-commit): `git diff --staged`, matching commit_review_gate.py's own
    `_staged_diff` -- the actual lines about to be committed.
  - In CI, in order: (1) the merge-base between HEAD and the MR's target branch, when
    `CI_MERGE_REQUEST_TARGET_BRANCH_NAME` is set (merge-request pipelines) -- covers every
    commit on the branch, not just the last one; (2) `CI_COMMIT_BEFORE_SHA`, when set and not
    the all-zero sentinel GitLab uses for a branch's first push (push pipelines to `main`,
    which `validate:pre-commit` also runs on -- this check must not go quiet there just because it
    is not an MR). If neither base is available (a `web`-triggered manual run, or a shallow
    clone missing the needed history), the check FAILS CLOSED with a clear message rather
    than passing silently -- a CI job that cannot determine what changed must not report
    green, since that is exactly the gap a `--no-verify` bypass or a broken checkout would
    hide.

Usage (from repo root):
    python scripts/check_no_em_dash.py
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DASHES = (chr(0x2014), chr(0x2013))


def _run(args: list[str], cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(args, cwd=cwd, capture_output=True, timeout=30)


def _staged_diff(root: Path) -> bytes | None:
    result = _run(["git", "diff", "--staged", "--no-renames", "--no-abbrev"], root)
    if result.returncode != 0:
        return None
    return result.stdout


_ALL_ZERO_SHA = "0" * 40


def _diff_against(root: Path, base_sha: str) -> bytes | None:
    result = _run(["git", "diff", "--no-renames", "--no-abbrev", base_sha, "HEAD"], root)
    if result.returncode != 0:
        return None
    return result.stdout


def _mr_target_base(root: Path) -> str | None:
    target = os.environ.get("CI_MERGE_REQUEST_TARGET_BRANCH_NAME")
    if not target:
        return None
    _run(["git", "fetch", "origin", target, "--depth=100"], root)
    merge_base = _run(["git", "merge-base", "HEAD", f"origin/{target}"], root)
    if merge_base.returncode != 0 or not merge_base.stdout.strip():
        return None
    return merge_base.stdout.decode().strip()


def _push_before_base(root: Path) -> str | None:
    before = os.environ.get("CI_COMMIT_BEFORE_SHA")
    if not before or before == _ALL_ZERO_SHA:
        return None
    check = _run(["git", "cat-file", "-e", before], root)
    if check.returncode != 0:
        # Not present locally (shallow clone) -- try to fetch just that commit.
        _run(["git", "fetch", "origin", before, "--depth=1"], root)
        check = _run(["git", "cat-file", "-e", before], root)
        if check.returncode != 0:
            return None
    return before


def _get_diff(root: Path) -> tuple[bytes | None, str]:
    if os.environ.get("CI"):
        base = _mr_target_base(root)
        if base:
            diff = _diff_against(root, base)
            if diff is not None:
                return diff, "CI (merge-base with MR target branch)"
        base = _push_before_base(root)
        if base:
            diff = _diff_against(root, base)
            if diff is not None:
                return diff, "CI (diff against CI_COMMIT_BEFORE_SHA)"
        return None, (
            "CI: no MR target branch and no usable CI_COMMIT_BEFORE_SHA -- cannot determine "
            "what changed (a web-triggered run, a branch's first push, or a shallow clone "
            "missing the needed history)"
        )
    diff = _staged_diff(root)
    if diff is not None:
        return diff, "staged"
    return None, "could not compute a staged diff (not a git repo, or git failed)"


def find_violations(diff: bytes) -> list[str]:
    violations = []
    current_file = None
    lineno = 0
    for raw_line in diff.split(b"\n"):
        try:
            line = raw_line.decode("utf-8")
        except UnicodeDecodeError:
            continue
        if line.startswith("+++ "):
            path = line[4:]
            current_file = path[2:] if path.startswith("b/") else path
            continue
        if line.startswith("@@"):
            # "@@ -a,b +c,d @@" -- c is the new-file starting line number.
            try:
                plus_part = line.split("+", 1)[1].split(" ", 1)[0]
                lineno = int(plus_part.split(",")[0]) - 1
            except (IndexError, ValueError):
                lineno = 0
            continue
        if line.startswith("+") and not line.startswith("+++"):
            lineno += 1
            if any(ch in line for ch in DASHES):
                violations.append(f"{current_file}:{lineno}: em-dash or en-dash on an added line")
        elif not line.startswith("-"):
            lineno += 1
    return violations


def main() -> int:
    diff, source = _get_diff(REPO_ROOT)
    if diff is None:
        print(f"Em-dash check: {source}")
        # In CI, "no diff available" must fail closed -- a job that cannot determine what
        # changed must not report green. Locally (no staged changes, or run outside a repo)
        # there is nothing to check and nothing to hide, so it passes.
        return 1 if os.environ.get("CI") else 0
    violations = find_violations(diff)
    if violations:
        print(f"Em-dash check FAILED (diff source: {source}):")
        for line in violations:
            print(f"  {line}")
        print("\nUse `--` instead, per engineering_standards.md §1.3. A pre-existing dash on "
              "an untouched line is not flagged -- only lines this diff adds.")
        return 1
    print(f"Em-dash check passed (diff source: {source}).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
