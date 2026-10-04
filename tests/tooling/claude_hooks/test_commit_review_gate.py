"""Tests for the review gate: verdict parsing, the cumulative diff hash, the round cap,
routing/role-file integrity, and the git `pre-commit` hook mode, exercised through a real
git hook. Runnable with `pytest` or directly: `python tests/tooling/claude_hooks/test_commit_review_gate.py`.
"""

import hashlib
import os
import re
import shutil
import subprocess
import sys
import tempfile

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
_HOOKS = os.path.join(_REPO_ROOT, ".claude", "hooks")
sys.path.insert(0, _HOOKS)

import commit_review_gate as crg  # noqa: E402
from commit_review_gate import (  # noqa: E402
    _base_ref,
    _diff_to_hash,
    _gate,
    _load_routing,
    _required_reviewers,
    _rounds,
    _sections,
    _staged_diff,
    _verdict,
)


_GIT = shutil.which("git")


def test_verdict_reads_the_operative_block():
    assert _verdict("VERDICT: PASS\nrisks_checked:\n- a\n- b") == "PASS"
    assert _verdict("VERDICT: FAIL\nfindings:\n- x") == "FAIL"
    assert _verdict("VERDICT: ESCALATE\nquestions:\n- q") == "ESCALATE"
    assert _verdict("no verdict here at all") is None


def test_verdict_ignores_example_text_before_the_real_one():
    body = ("A FAIL would read `VERDICT: FAIL`, but I found nothing wrong.\n"
            "VERDICT: PASS\nrisks_checked:\n- a\n- b")
    assert _verdict(body) == "PASS"


def test_prose_fail_is_not_a_reviewer_fail():
    # the change-3 bug: 'VERDICT: FAIL' in preamble prose must not count as a fail
    text = ("Reviewers must block on VERDICT: FAIL.\n\n"
            "## scope-auditor\nVERDICT: PASS\nrisks_checked:\n- a\n- b\n")
    sections = _sections(text)
    verdicts = {n: _verdict(b) for n, b in sections.items() if n != "_preamble"}
    assert verdicts == {"scope-auditor": "PASS"}
    assert "FAIL" not in verdicts.values()


def test_a_real_reviewer_fail_is_still_caught():
    text = ("## scope-auditor\nVERDICT: PASS\nrisks_checked:\n- a\n- b\n\n"
            "## cto-reviewer\nVERDICT: FAIL\nfindings:\n- hooks/x.py:1 broke a rule\n")
    verdicts = {n: _verdict(b) for n, b in _sections(text).items() if n != "_preamble"}
    assert verdicts["cto-reviewer"] == "FAIL"


def test_escalation_answer_is_scoped_to_its_own_section():
    # an answered escalation in one section must not clear an unanswered one elsewhere
    text = ("## scope-auditor\nVERDICT: ESCALATE\nquestions:\n- q1\nCPO ANSWER: go with A\n\n"
            "## cto-reviewer\nVERDICT: ESCALATE\nquestions:\n- q2\n")
    sections = _sections(text)
    answered = "CPO ANSWER:" in sections["scope-auditor"]
    unanswered = "CPO ANSWER:" not in sections["cto-reviewer"]
    assert answered and unanswered


def _git(repo, *args):
    subprocess.run([_GIT, *args], cwd=repo, check=True,
                   capture_output=True, timeout=30)


def test_rounds_defaults_to_one():
    assert _rounds("diff_sha256: abc\n## scope-auditor\nVERDICT: PASS\n") == 1


def test_rounds_parses_explicit_value():
    assert _rounds("diff_sha256: abc\nrounds: 3\n## x\nVERDICT: PASS\n") == 3


def test_base_ref_none_in_a_commit_less_repo():
    if not _GIT:
        print("skip (no git on PATH)")
        return
    with tempfile.TemporaryDirectory() as repo:
        _git(repo, "init", "-q")
        assert _base_ref(repo) is None, "no ref can resolve before the first commit"


def test_diff_to_hash_covers_earlier_commits_on_the_branch():
    # The Phase-3 fix: a multi-commit branch's reviewed diff must cover the
    # WHOLE branch, not just what happens to be staged right now.
    if not _GIT:
        print("skip (no git on PATH)")
        return
    with tempfile.TemporaryDirectory() as repo:
        _git(repo, "init", "-q", "-b", "main")
        _git(repo, "config", "user.email", "t@t.t")
        _git(repo, "config", "user.name", "t")
        with open(os.path.join(repo, "base.txt"), "w", encoding="utf-8") as f:
            f.write("base\n")
        _git(repo, "add", "base.txt")
        _git(repo, "commit", "-m", "base")
        _git(repo, "checkout", "-b", "feature")
        with open(os.path.join(repo, "file1.txt"), "w", encoding="utf-8") as f:
            f.write("one\n")
        _git(repo, "add", "file1.txt")
        _git(repo, "commit", "-m", "first")

        assert _staged_diff(repo) == b"", "nothing should be staged right now"
        cumulative = _diff_to_hash(repo)
        assert b"file1.txt" in cumulative, (
            "cumulative diff must include the earlier commit even with "
            "nothing currently staged")

        with open(os.path.join(repo, "file2.txt"), "w", encoding="utf-8") as f:
            f.write("two\n")
        _git(repo, "add", "file2.txt")
        _git(repo, "commit", "-m", "second")
        cumulative2 = _diff_to_hash(repo)
        assert b"file1.txt" in cumulative2 and b"file2.txt" in cumulative2, (
            "cumulative diff must grow to cover every commit since the base")


def _routing_only_repo(repo: str) -> None:
    """A minimal repo with routing that requires no reviewer (empty
    'always'/'paths'), so round-cap tests isolate that one behavior."""
    os.makedirs(os.path.join(repo, ".claude", "task"))
    with open(os.path.join(repo, ".claude", "review_routing.json"), "w", encoding="utf-8") as f:
        f.write('{"always": [], "paths": {}}')
    with open(os.path.join(repo, "file.txt"), "w", encoding="utf-8") as f:
        f.write("hello\n")
    _git(repo, "add", "file.txt")


def test_round_cap_blocks_without_cpo_answer():
    if not _GIT:
        print("skip (no git on PATH)")
        return
    with tempfile.TemporaryDirectory() as repo:
        _git(repo, "init", "-q")
        _git(repo, "config", "user.email", "t@t.t")
        _git(repo, "config", "user.name", "t")
        _routing_only_repo(repo)
        live = hashlib.sha256(_diff_to_hash(repo)).hexdigest()
        review = (f"diff_sha256: {live}\nrounds: 4\n"
                  "## scope-auditor\nVERDICT: PASS\nrisks_checked:\n- a\n- b\n")
        with open(os.path.join(repo, ".claude", "task", "review.md"), "w", encoding="utf-8") as f:
            f.write(review)
        reason = _gate(repo)
        assert reason and "round" in reason.lower()


def _gate_on_review(header: str, verdicts: str) -> str | None:
    """_gate on a routing-only repo whose review.md is the live hash, then
    `header`, then the reviewer `verdicts` sections."""
    with tempfile.TemporaryDirectory() as repo:
        _git(repo, "init", "-q")
        _git(repo, "config", "user.email", "t@t.t")
        _git(repo, "config", "user.name", "t")
        _routing_only_repo(repo)
        live = hashlib.sha256(_diff_to_hash(repo)).hexdigest()
        with open(os.path.join(repo, ".claude", "task", "review.md"), "w", encoding="utf-8") as f:
            f.write(f"diff_sha256: {live}\n{header}\n{verdicts}")
        return _gate(repo)


_PASS = "## scope-auditor\nVERDICT: PASS\nrisks_checked:\n- a\n- b\n"
_FAIL = "## platform-reviewer\nVERDICT: FAIL\nfindings:\n- [design] x\n"


def test_round_cap_blocks_an_answer_that_files_nothing():
    if not _GIT:
        print("skip (no git on PATH)")
        return
    reason = _gate_on_review("rounds: 5\nCPO ANSWER: run another round\n", _PASS)
    assert reason and "file the rest" in reason


def test_round_cap_allows_an_answer_naming_the_follow_up_issue():
    if not _GIT:
        print("skip (no git on PATH)")
        return
    assert _gate_on_review("rounds: 5\nCPO ANSWER: commit what is proven,\n"
                           "the rest is filed as #31\n", _PASS) is None


def test_round_cap_issue_ref_outside_the_answer_does_not_count():
    if not _GIT:
        print("skip (no git on PATH)")
        return
    reason = _gate_on_review("rounds: 4\nRefs #30\n\nCPO ANSWER: run another round\n", _PASS)
    assert reason and "file the rest" in reason


def test_past_the_cap_a_filed_answer_lets_fail_verdicts_through():
    if not _GIT:
        print("skip (no git on PATH)")
        return
    assert _gate_on_review("rounds: 4\nCPO ANSWER: commit what is proven, rest in #31\n",
                           _PASS + _FAIL) is None


def test_under_the_cap_a_filed_answer_does_not_override_fail():
    if not _GIT:
        print("skip (no git on PATH)")
        return
    reason = _gate_on_review("rounds: 2\nCPO ANSWER: commit what is proven, rest in #31\n",
                             _PASS + _FAIL)
    assert reason and "FAIL" in reason


def test_at_the_cap_a_filed_answer_lets_fail_verdicts_through():
    if not _GIT:
        print("skip (no git on PATH)")
        return
    assert _gate_on_review("rounds: 3\nCPO ANSWER: commit what is proven, rest in #31\n",
                           _PASS + _FAIL) is None


def test_at_the_cap_a_fail_without_a_filed_answer_names_the_exits():
    if not _GIT:
        print("skip (no git on PATH)")
        return
    reason = _gate_on_review("rounds: 3\n", _PASS + _FAIL)
    assert reason and "file the rest" in reason


def test_an_issue_ref_before_the_answer_does_not_count():
    if not _GIT:
        print("skip (no git on PATH)")
        return
    reason = _gate_on_review("rounds: 4\nQ: extend #29?\nCPO ANSWER: yes, one more round\n",
                             _PASS)
    assert reason and "file the rest" in reason


def test_round_cap_does_not_trip_under_the_cap():
    if not _GIT:
        print("skip (no git on PATH)")
        return
    with tempfile.TemporaryDirectory() as repo:
        _git(repo, "init", "-q")
        _git(repo, "config", "user.email", "t@t.t")
        _git(repo, "config", "user.name", "t")
        _routing_only_repo(repo)
        live = hashlib.sha256(_diff_to_hash(repo)).hexdigest()
        review = (f"diff_sha256: {live}\nrounds: 2\n"
                  "## scope-auditor\nVERDICT: PASS\nrisks_checked:\n- a\n- b\n")
        with open(os.path.join(repo, ".claude", "task", "review.md"), "w", encoding="utf-8") as f:
            f.write(review)
        assert _gate(repo) is None


def test_staged_diff_excludes_the_task_dir():
    # The self-reference fix: staging .claude/task/** (where review.md lives) must
    # NOT change the staged-diff hash, so review.md recording that hash can't
    # deadlock the gate.
    if not _GIT:
        print("skip (no git on PATH)")
        return
    with tempfile.TemporaryDirectory() as repo:
        _git(repo, "init", "-q")
        _git(repo, "config", "user.email", "t@t.t")
        _git(repo, "config", "user.name", "t")
        # A real change, staged.
        with open(os.path.join(repo, "model.sql"), "w", encoding="utf-8") as f:
            f.write("select 1\n")
        _git(repo, "add", "model.sql")
        hash_before = hashlib.sha256(_staged_diff(repo)).hexdigest()
        # Now stage a review artifact under .claude/task/ -- must not move the hash.
        os.makedirs(os.path.join(repo, ".claude", "task"))
        with open(os.path.join(repo, ".claude", "task", "review.md"), "w", encoding="utf-8") as f:
            f.write("diff_sha256: " + hash_before + "\n## scope-auditor\nVERDICT: PASS\n")
        _git(repo, "add", ".claude/task/review.md")
        hash_after = hashlib.sha256(_staged_diff(repo)).hexdigest()
        assert hash_after == hash_before, "staging .claude/task/ changed the hash"
        # Sanity: a real second change DOES move the hash (exclusion isn't too broad).
        with open(os.path.join(repo, "model2.sql"), "w", encoding="utf-8") as f:
            f.write("select 2\n")
        _git(repo, "add", "model2.sql")
        assert hashlib.sha256(_staged_diff(repo)).hexdigest() != hash_before


def _repo_with_gate_hook(repo: str) -> None:
    """A repo whose real git pre-commit hook runs this gate, like pre-commit does."""
    _git(repo, "init", "-q")
    _git(repo, "config", "user.email", "t@t.t")
    _git(repo, "config", "user.name", "t")
    _routing_only_repo(repo)
    hook = os.path.join(repo, ".git", "hooks", "pre-commit")
    with open(hook, "w", encoding="utf-8", newline="\n") as f:
        f.write('#!/bin/sh\nexec "{}" "{}" --git-hook\n'.format(
            sys.executable.replace("\\", "/"), os.path.abspath(crg.__file__).replace("\\", "/")))
    os.chmod(hook, 0o755)


def _commit_from_elsewhere(repo: str, cwd: str, claude: bool):
    env = {k: v for k, v in os.environ.items() if k != "CLAUDECODE"}
    if claude:
        env["CLAUDECODE"] = "1"
    return subprocess.run([_GIT, "-C", repo, "commit", "-q", "-m", "x"], cwd=cwd, env=env,
                          capture_output=True, text=True, timeout=60)


def test_git_hook_refuses_an_unreviewed_commit_from_claude_code_wherever_it_is_run():
    if not _GIT:
        print("skip (no git on PATH)")
        return
    with tempfile.TemporaryDirectory() as repo, tempfile.TemporaryDirectory() as elsewhere:
        _repo_with_gate_hook(repo)
        refused = _commit_from_elsewhere(repo, elsewhere, claude=True)
        assert refused.returncode != 0 and "REVIEW GATE:" in refused.stderr, refused.stderr
        m = re.search(r'python "([^"]+)" --diff-hash', refused.stderr)
        assert m and os.path.isfile(m.group(1)), refused.stderr
        live = hashlib.sha256(_diff_to_hash(repo)).hexdigest()
        with open(os.path.join(repo, ".claude", "task", "review.md"), "w", encoding="utf-8") as f:
            f.write(f"diff_sha256: {live}\n")
        allowed = _commit_from_elsewhere(repo, elsewhere, claude=True)
        assert allowed.returncode == 0, allowed.stderr


def test_git_hook_ignores_commits_not_from_claude_code():
    if not _GIT:
        print("skip (no git on PATH)")
        return
    with tempfile.TemporaryDirectory() as repo, tempfile.TemporaryDirectory() as elsewhere:
        _repo_with_gate_hook(repo)
        result = _commit_from_elsewhere(repo, elsewhere, claude=False)
        assert result.returncode == 0, result.stderr


def test_git_hook_fails_open_when_its_helper_cannot_be_imported():
    with tempfile.TemporaryDirectory() as hooks:
        shutil.copy(crg.__file__, hooks)
        with open(os.path.join(hooks, "_command_utils.py"), "w", encoding="utf-8") as f:
            f.write("raise RuntimeError('broken helper')\n")
        env = dict(os.environ, CLAUDECODE="1")
        result = subprocess.run([sys.executable, os.path.join(hooks, "commit_review_gate.py"), "--git-hook"],
                                env=env, capture_output=True, text=True, timeout=30)
        assert result.returncode == 0, result.stderr


def test_git_hook_is_inactive_in_a_checkout_without_review_routing():
    if not _GIT:
        print("skip (no git on PATH)")
        return
    with tempfile.TemporaryDirectory() as repo, tempfile.TemporaryDirectory() as elsewhere:
        _repo_with_gate_hook(repo)
        os.remove(os.path.join(repo, ".claude", "review_routing.json"))
        result = _commit_from_elsewhere(repo, elsewhere, claude=True)
        assert result.returncode == 0, result.stderr


def test_diff_hash_is_the_same_from_a_subdirectory():
    if not _GIT:
        print("skip (no git on PATH)")
        return
    with tempfile.TemporaryDirectory() as repo:
        _git(repo, "init", "-q")
        _routing_only_repo(repo)
        sub = os.path.join(repo, "a", "b")
        os.makedirs(sub)
        env = {k: v for k, v in os.environ.items() if k != "CLAUDE_PROJECT_DIR"}

        def printed(cwd):
            return subprocess.run(
                [sys.executable, crg.__file__, "--diff-hash"], capture_output=True,
                text=True, cwd=cwd, env=env, timeout=30).stdout.strip()

        at_root = printed(repo)
        assert at_root == hashlib.sha256(_diff_to_hash(repo)).hexdigest()
        assert printed(sub) == at_root


def test_guard_paths_route_to_platform_reviewer():
    routing = _load_routing(_REPO_ROOT)
    assert routing is not None, "review_routing.json should load from the repo root"
    for path in (".claude/agents/scope-auditor.md", ".claude/hooks/commit_review_gate.py",
                 ".claude/settings.json", "tests/tooling/claude_hooks/test_x.py"):
        assert "platform-reviewer" in _required_reviewers([path], routing), path
    assert _required_reviewers(["README.md"], routing) == {"scope-auditor"}


def test_every_routed_reviewer_has_a_role_file():
    routing = _load_routing(_REPO_ROOT)
    names = set(routing.get("always") or [])
    for reviewers in (routing.get("paths") or {}).values():
        names.update(reviewers)
    agents = os.path.join(_REPO_ROOT, ".claude", "agents")
    missing = sorted(n for n in names if not os.path.isfile(os.path.join(agents, f"{n}.md")))
    assert not missing, f"routed reviewers without a role file: {missing}"


if __name__ == "__main__":
    _failed = 0
    for _name, _fn in sorted(globals().items()):
        if _name.startswith("test_") and callable(_fn):
            try:
                _fn()
                print(f"ok   {_name}")
            except Exception as e:  # noqa: BLE001 -- surface subprocess/setup errors too
                _failed += 1
                print(f"FAIL {_name}: {type(e).__name__}: {e}")
    print("all tests passed" if not _failed else f"{_failed} test(s) failed")
    sys.exit(1 if _failed else 0)
