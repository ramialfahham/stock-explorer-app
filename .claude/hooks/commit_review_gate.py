#!/usr/bin/env python
"""The blinded review gate: a git `pre-commit` hook that blocks Claude Code's commits
until the change has been reviewed.

pre-commit runs it (hook id `review-gate`) inside the checkout git is committing, so the
checkout is always the right one, however the command was written (`cd`, `git -C`, a
worktree, PowerShell). It applies only when CLAUDECODE=1; the owner's own commits pass.
On a commit, it:
  1. hashes the CUMULATIVE diff -- everything already committed on this branch
     since it split from the base branch (main/master, local or remote),
     PLUS what's currently staged -- not just the staged diff alone. A
     multi-commit branch's review must cover the whole branch, not silently
     just its last increment; this also matches what scope-auditor.md says
     its input is ("the cumulative branch diff vs the base branch").
  2. works out which reviewers are required for the changed files
     (.claude/review_routing.json in the project),
  3. reads .claude/task/review.md and BLOCKS the commit unless:
       - the recorded diff_sha256 matches the cumulative diff (so the review
         covers exactly what the branch will contain after this commit),
       - every required reviewer has a verdict and none is FAIL,
       - every ESCALATE has a recorded "CPO ANSWER:",
       - once review.md's optional `rounds:` counter reaches the cap with a FAIL
         still standing, there is no further round: the only exits are "commit
         what is proven and file the rest" (a "CPO ANSWER:" followed in its
         paragraph by the follow-up issue `#N`, which also lets remaining FAIL
         verdicts through) or stop.
         A count above the cap is refused without that answer. `rounds:` is
         SELF-REPORTED (whoever re-reviews increments it) -- the hook enforces
         the cap once recorded, it doesn't independently derive the count.
A commit is exempt when the branch's whole cumulative diff touches only
bookkeeping files (.claude/task/**, active_work.md). Fails OPEN on any error -- a gate bug must never block your workflow.

Wired in .pre-commit-config.yaml as `python .claude/hooks/commit_review_gate.py --git-hook`.
Run with --diff-hash, from anywhere in the checkout, to print the diff hash for review.md
(--staged-hash also accepted, for anything already using that name).
"""

from __future__ import annotations

import fnmatch
import hashlib
import json
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

ROUTING_REL = os.path.join(".claude", "review_routing.json")
REVIEW_REL = os.path.join(".claude", "task", "review.md")

# Candidate base-branch refs, checked in order -- first one that actually
# resolves wins. Local before remote, main before master; a repo can have
# either remote name depending on which provider it was migrated to/from.
_BASE_REF_CANDIDATES = (
    "main", "master",
    "origin/main", "origin/master",
    "gitlab/main", "gitlab/master",
)
_ROUNDS_RE = re.compile(r"^rounds:\s*(\d+)", re.MULTILINE)
_ROUNDS_CAP = 3
_ISSUE_REF_RE = re.compile(r"#\d+")


def _rev_parse_ok(root: str, ref: str) -> bool:
    return subprocess.run(
        ["git", "rev-parse", "--verify", "--quiet", ref],
        cwd=root, capture_output=True, timeout=10,
    ).returncode == 0


def _base_ref(root: str) -> str | None:
    for ref in _BASE_REF_CANDIDATES:
        if _rev_parse_ok(root, ref):
            return ref
    return None


def _merge_base(root: str, base_ref: str) -> str | None:
    out = subprocess.run(
        ["git", "merge-base", base_ref, "HEAD"],
        cwd=root, capture_output=True, text=True, timeout=10,
    ).stdout.strip()
    return out or None


def _staged_diff(root: str) -> bytes:
    # --no-renames + --no-abbrev pin the bytes so the hash is reproducible for
    # identical staged content (stable paths, full blob ids).
    # Exclude .claude/task/** so the hash covers ONLY the real change: review.md
    # records this very hash, so hashing it in would be a self-reference that can
    # never match once review.md is staged (the reported deadlock). The live gate
    # and the --diff-hash printer both go through _diff_to_hash, which calls this
    # only when no merge-base exists; its own `git diff --cached` repeats the
    # same exclusion, so both paths hash the same scope.
    return subprocess.run(
        ["git", "diff", "--staged", "--no-renames", "--no-abbrev",
         "--", ".", ":(exclude).claude/task"],
        cwd=root, capture_output=True, timeout=30,
    ).stdout


def _diff_to_hash(root: str) -> bytes:
    """The diff review.md's hash must cover: everything since the branch split
    from its base, PLUS what's currently staged. Falls back to staged-only
    (the old behavior) when no base ref is discoverable at all -- e.g. a
    shallow clone with no main/master ref reachable -- so this never blocks on
    an environment quirk; it only widens coverage when it safely can."""
    base = _base_ref(root)
    merge_base = _merge_base(root, base) if base else None
    if not merge_base:
        return _staged_diff(root)
    # `git diff --cached <commit>`: commit vs the INDEX (staged state), which
    # for a clean working tree is exactly "everything committed since
    # <commit> plus what's staged now" -- the cumulative diff this commit is
    # about to extend the branch to.
    return subprocess.run(
        ["git", "diff", "--cached", "--no-renames", "--no-abbrev", merge_base,
         "--", ".", ":(exclude).claude/task"],
        cwd=root, capture_output=True, timeout=30,
    ).stdout


def _staged_paths(root: str) -> list[str]:
    out = subprocess.run(
        ["git", "diff", "--staged", "--name-only", "-z"],
        cwd=root, capture_output=True, text=True, timeout=30,
    ).stdout
    return [p.replace("\\", "/") for p in out.split("\0") if p]


def _load_routing(root: str) -> dict | None:
    try:
        with open(os.path.join(root, ROUTING_REL), encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def _required_reviewers(paths: list[str], routing: dict) -> set[str]:
    required = set(routing.get("always") or [])
    for path in paths:
        for pattern, reviewers in (routing.get("paths") or {}).items():
            if fnmatch.fnmatch(path, pattern):
                required.update(reviewers)
    return required


def _artifact_only(paths: list[str], routing: dict) -> bool:
    never = routing.get("artifact_only_never") or []
    if any(fnmatch.fnmatch(p, pat) for p in paths for pat in never):
        return False
    pats = routing.get("artifact_only") or []
    return bool(paths) and all(
        any(fnmatch.fnmatch(p, pat) for pat in pats) for p in paths
    )


def _sections(text: str) -> dict[str, str]:
    """Map '## name' -> body. Text before the first header is '_preamble'."""
    sections, name, buf = {}, "_preamble", []
    for line in text.splitlines():
        m = re.match(r"^##\s+(\S+)", line)
        if m:
            sections[name] = "\n".join(buf)
            name, buf = m.group(1), []
        else:
            buf.append(line)
    sections[name] = "\n".join(buf)
    return sections


_VERDICT_RE = re.compile(r"^VERDICT:\s*(PASS|FAIL|ESCALATE)\b", re.MULTILINE)


def _verdict(body: str) -> str | None:
    """The operative verdict in a reviewer's section body, or None. Reviewers end
    with the verdict block, so the LAST match wins -- an earlier 'VERDICT: X' in
    prose or a quoted example doesn't override the real one."""
    matches = _VERDICT_RE.findall(body)
    return matches[-1] if matches else None


def _cumulative_paths(root: str) -> list[str]:
    """Same cumulative scope as _diff_to_hash, as a path list -- so which
    reviewers are required (and whether this is bookkeeping-only) reflects
    the whole branch, not just this commit's staged files. Falls back to the
    staged-only list under the same no-base-ref condition as _diff_to_hash."""
    base = _base_ref(root)
    merge_base = _merge_base(root, base) if base else None
    if not merge_base:
        return _staged_paths(root)
    out = subprocess.run(
        ["git", "diff", "--cached", "--name-only", "-z", merge_base],
        cwd=root, capture_output=True, text=True, timeout=30,
    ).stdout
    return [p.replace("\\", "/") for p in out.split("\0") if p]


def _rounds(text: str) -> int:
    m = _ROUNDS_RE.search(text)
    return int(m.group(1)) if m else 1


def _files_the_rest(text: str) -> bool:
    """True if a 'CPO ANSWER:' is followed, in its paragraph, by an issue ref (`#N`)."""
    return any("CPO ANSWER:" in para
               and _ISSUE_REF_RE.search(para[para.index("CPO ANSWER:"):])
               for para in re.split(r"\n\s*\n", text))


def _cap_message(rounds: int) -> str:
    return (f"REVIEW GATE: review.md reports round {rounds}; the cap is "
            f"{_ROUNDS_CAP}. No further round. Two exits, the owner's choice: "
            "commit what is proven and file the rest (record a 'CPO ANSWER:' "
            "followed in the same paragraph by the follow-up issue, #N, in "
            "review.md; remaining FAIL verdicts then no longer block), or stop.")


def _gate(root: str) -> str | None:
    staged = _staged_paths(root)
    if not staged:
        return None  # nothing staged: let git complain
    routing = _load_routing(root)
    if routing is None:
        return None  # no routing anywhere: gate inactive (fail open)
    paths = _cumulative_paths(root) or staged
    if _artifact_only(paths, routing):
        return None  # bookkeeping-only for the WHOLE branch: exempt
    review_path = os.path.join(root, REVIEW_REL)
    if not os.path.isfile(review_path):
        # The hash command names THIS file by absolute path; run it from inside the
        # checkout being committed (it hashes that checkout).
        return ("REVIEW GATE: no review found. Stage the change, run the required "
                "reviewers, and write .claude/task/review.md with the diff hash from: "
                f"python \"{os.path.abspath(__file__)}\" --diff-hash -- then commit.")
    text = open(review_path, encoding="utf-8", errors="replace").read()
    live = hashlib.sha256(_diff_to_hash(root)).hexdigest()
    m = re.search(r"diff_sha256:\s*([0-9a-fA-F]{64})", text)
    if not m or m.group(1).lower() != live:
        return ("REVIEW GATE: the reviewed diff doesn't match the branch's current "
                "cumulative diff (everything committed since the base branch, plus "
                "what's staged now) -- re-run the reviewers, update review.md and stage it "
                "(pre-commit hides unstaged changes while hooks run). "
                f"Current hash: {live} (from: python \"{os.path.abspath(__file__)}\" --diff-hash)")
    rounds = _rounds(text)
    filed = _files_the_rest(text)
    if rounds > _ROUNDS_CAP and not filed:
        return _cap_message(rounds)
    # Read each verdict from its reviewer SECTION, not the raw text -- a
    # 'VERDICT: FAIL' in prose or a quoted example must not block a review where
    # every real verdict passed, and a 'CPO ANSWER:' for one escalation must not
    # offset a different unanswered one.
    sections = _sections(text)
    verdicts = {name: _verdict(body) for name, body in sections.items()
                if name != "_preamble"}
    for reviewer in sorted(_required_reviewers(paths, routing)):
        if not verdicts.get(reviewer):
            return (f"REVIEW GATE: required reviewer '{reviewer}' has no verdict for "
                    "the changed files (see review_routing.json). Run it and record "
                    "its section in review.md.")
    failed = sorted(n for n, v in verdicts.items() if v == "FAIL")
    if failed and rounds >= _ROUNDS_CAP and not filed:
        return _cap_message(rounds)
    if failed and rounds < _ROUNDS_CAP:
        return (f"REVIEW GATE: reviewer '{failed[0]}' verdict is FAIL. Fix the "
                "findings and re-review.")
    for name in sorted(verdicts):
        if verdicts[name] == "ESCALATE" and "CPO ANSWER:" not in sections.get(name, ""):
            return (f"REVIEW GATE: reviewer '{name}' escalated with no recorded "
                    "'CPO ANSWER:'. Get the owner's decision, write it under the "
                    "question, then commit.")
    return None


def git_hook(root: str | None) -> int:
    """The `pre-commit` hook: 1 (commit refused, reason on stderr) or 0."""
    if not root:
        return 0
    reason = _gate(root)
    if reason:
        print(reason, file=sys.stderr)
        return 1
    return 0


def main(argv: list[str]) -> int:
    # --diff-hash is the current name (it's the cumulative diff, not just
    # staged); --staged-hash kept as an alias so nothing that already calls
    # it breaks. The helper import is here, not at module level, so a broken
    # helper is caught by the fail-open below instead of blocking a commit.
    from _command_utils import from_claude_code, git_toplevel

    if "--diff-hash" in argv or "--staged-hash" in argv:
        print(hashlib.sha256(_diff_to_hash(git_toplevel() or os.getcwd())).hexdigest())
        return 0
    if "--git-hook" in argv:
        return git_hook(git_toplevel()) if from_claude_code() else 0
    print("usage: commit_review_gate.py --git-hook | --diff-hash", file=sys.stderr)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except Exception:
        sys.exit(0)  # fail open: a gate bug must never block a commit, the owner's included
