"""Tests for _command_utils, shared by the Claude-side hooks and the git hooks:
git-subcommand detection, quote stripping, the git-hook bypass scan, and the checkout
toplevel a git hook runs in.

Runnable with `pytest` or directly: `python tests/tooling/claude_hooks/test_command_utils.py`.
"""

import os
import subprocess
import sys
import tempfile

_HOOKS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", ".claude", "hooks")
sys.path.insert(0, _HOOKS)

from _command_utils import (  # noqa: E402
    _degroup,
    git_subcommand,
    git_toplevel,
    hook_bypass,
    is_commit_subcommand,
    simple_commands,
    strip_quoted_and_heredoc,
)


def test_hook_bypass_finds_the_usual_spellings():
    cases = [
        ("git commit --no-verify -m x", "`--no-verify`"),
        ("git commit --no-verif -m x", "`--no-verify`"),
        ("git commit --no-veri -m x", "`--no-verify`"),
        ("git commit -m x --no-verify; echo done", "`--no-verify`"),
        ("git add a; if ($?) { git commit -m x --no-verify}", "`--no-verify`"),
        ("(cd wt && git commit --no-verify -m x)", "`--no-verify`"),
        ("& git.exe commit --no-verify -m x", "`--no-verify`"),
        ("git commit -n -m x", "`-n`"),
        ("git commit -nm x", "`-n`"),
        ("git commit -anm x", "`-n`"),
        ("git commit -qn -m x", "`-n`"),
        ("git -c core.hooksPath=/dev/null commit -m x", "`core.hooksPath`"),
        ('git -c "core.hooksPath=/dev/null" commit -m x', "`core.hooksPath`"),
        ("git config core.hooksPath /tmp/none", "`core.hooksPath`"),
        ("git config set core.hooksPath /tmp/none", "`core.hooksPath`"),
        ("SKIP=review-gate git commit -m x", "`SKIP`"),
        ("export SKIP=gitleaks; git commit -m x", "`SKIP`"),
        ('$env:SKIP="review-gate"; git commit -m x', "`SKIP`"),
        ("Set-Item Env:SKIP review-gate; git commit -m x", "`SKIP`"),
        ("CLAUDECODE=0 git commit -m x", "`CLAUDECODE`"),
        ("env -u CLAUDECODE git commit -m x", "`CLAUDECODE`"),
        ("$env:CLAUDECODE=''; git commit -m x", "`CLAUDECODE`"),
        ("Remove-Item Env:CLAUDECODE; git commit -m x", "`CLAUDECODE`"),
        ("Remove-Item -Path Env:\\CLAUDECODE; git commit -m x", "`CLAUDECODE`"),
        ("Set-Item -Path Env:\\SKIP -Value review-gate; git commit -m x", "`SKIP`"),
        ("unset SKIP; git commit -m x", "`SKIP`"),
        ("[Environment]::SetEnvironmentVariable('CLAUDECODE', $null); git commit -m x", "`CLAUDECODE`"),
        ('[Environment]::SetEnvironmentVariable("SKIP","review-gate"); git commit -m x', "`SKIP`"),
        ('Remove-Item "Env:\\CLAUDECODE"; git commit -m x', "`CLAUDECODE`"),
        ("Set-Item -Path 'Env:SKIP' -Value review-gate; git commit -m x", "`SKIP`"),
    ]
    for command, expected in cases:
        assert hook_bypass(command) == expected, command


def test_hook_bypass_ignores_mentions_and_non_committing_commands():
    for command in (
        'git commit -m "never use --no-verify, SKIP= or CLAUDECODE here"',
        "git commit -F - <<'EOF'\nDon't use --no-verify or SKIP=x.\nEOF",
        "git log --grep commit -n 5",
        "git push -n gitlab b:b",
        "git push --no-verify gitlab b:b",
        "git push gitlab claudecode-env:claudecode-env",
        "git commit -m x && echo skip",
        "git commit -mfinal",
        "git commit -uno -m x",
        "git config --get core.hooksPath",
        "git config --unset core.hooksPath",
        "git config core.hooksPath",
        "git config get core.hooksPath",
        "git config unset core.hooksPath",
        "cd /c/work/claudecode && git commit -m x",
        'git commit -m "CLAUDECODE"',
        "git commit -m \"docs: explain 'Env:SKIP' handling\"",
        "git commit -m \"call SetEnvironmentVariable('CLAUDECODE', x) in docs\"",
        "git commit -m 'use \"Env:SKIP\" carefully'",
        "git commit -m 'Env:SKIP'",
        "git commit -m x && git push gitlab feature-claudecode:feature-claudecode",
        "git commit -m @'\nGate as a git hook; the owner's commits pass.\nActs only when CLAUDECODE=1,"
        " never with --no-verify.\n'@",
        "SKIP=gitleaks pre-commit run --all-files",
        "git config user.name x",
        "git commit -m x",
        "git push gitlab feature:feature",
        "",
    ):
        assert hook_bypass(command) is None, command


def test_stripping_keeps_a_placeholder_so_options_keep_their_slot():
    stripped = strip_quoted_and_heredoc('git commit -m "msg" file.py').split()
    assert stripped[-1] == "file.py"
    glued = strip_quoted_and_heredoc('git -c user.name="A B" commit --amend').split()
    assert git_subcommand(glued) == "commit" and "--amend" in glued


def test_git_toplevel_from_a_subdirectory_and_outside_a_checkout():
    with tempfile.TemporaryDirectory() as repo, tempfile.TemporaryDirectory() as other:
        subprocess.run(["git", "init", "-q", repo], check=True)
        sub = os.path.join(repo, "a", "b")
        os.makedirs(sub)
        top = os.path.normcase(os.path.realpath(repo))
        assert os.path.normcase(os.path.realpath(git_toplevel(sub))) == top
        outside = git_toplevel(other)
        assert outside is None or os.path.normcase(os.path.realpath(outside)) != top


def test_plain_subcommand():
    assert git_subcommand("git commit".split()) == "commit"
    assert git_subcommand("git push origin main".split()) == "push"
    assert git_subcommand("git log --oneline".split()) == "log"
    assert git_subcommand("git status".split()) == "status"


def test_global_options_are_skipped():
    # the gap this fixes: a real commit/push hidden behind global options
    assert git_subcommand("git -c user.email=x@y.z commit -m m".split()) == "commit"
    assert git_subcommand("git -C /repo commit".split()) == "commit"
    assert git_subcommand("git --no-pager commit".split()) == "commit"
    assert git_subcommand("git -c http.x=y push origin main".split()) == "push"


def test_word_commit_as_argument_is_not_the_subcommand():
    assert git_subcommand("git log --grep commit".split()) == "log"
    assert git_subcommand("git show HEAD:commit".split()) == "show"


def test_commit_tree_is_not_commit():
    # a different subcommand that merely starts with 'commit'
    assert git_subcommand("git commit-tree -p HEAD".split()) == "commit-tree"


def test_non_git_is_none():
    assert git_subcommand("echo git commit".split()) is None
    assert git_subcommand("".split()) is None
    assert git_subcommand([]) is None


def test_degroup_strips_wrapping_punctuation():
    assert _degroup(["(git", "commit", "-m", "x)"]) == ["git", "commit", "-m", "x"]
    assert _degroup(["{", "git", "commit", "-m", "x"]) == ["git", "commit", "-m", "x"]
    assert _degroup(["git", "commit"]) == ["git", "commit"]  # unwrapped: unchanged
    assert _degroup([]) == []


def test_subshell_wrapped_commit_is_still_detected():
    # (git commit -m x) -- a single-command subshell with no operator inside,
    # so simple_commands doesn't split it; without degrouping this would be
    # invisible to every guard in the repo
    for part in simple_commands("(git commit -m x)"):
        assert git_subcommand(part.split()) == "commit"


def test_brace_grouped_commit_is_still_detected():
    # { git commit -m x; } splits on the internal ';', so the group's braces
    # end up attached to different simple-commands than in the subshell case
    parts = list(simple_commands("{ git commit -m x; }"))
    assert any(git_subcommand(p.split()) == "commit" for p in parts)


def test_is_commit_subcommand_excludes_dry_run():
    # every guard that cares about a REAL commit shares this predicate now --
    # a --dry-run commits nothing, so it must never read as a commit
    assert is_commit_subcommand("git commit -m x".split()) is True
    assert is_commit_subcommand("git commit --dry-run".split()) is False
    assert is_commit_subcommand("git log --grep commit".split()) is False
    assert is_commit_subcommand("git status".split()) is False


def test_grouping_does_not_create_a_false_positive():
    # a group around something that ISN'T a commit must still resolve to
    # None, not accidentally become "commit" through overzealous stripping
    for part in simple_commands("(git status)"):
        assert git_subcommand(part.split()) != "commit"


if __name__ == "__main__":
    _failed = 0
    for _name, _fn in sorted(globals().items()):
        if _name.startswith("test_") and callable(_fn):
            try:
                _fn()
                print(f"ok   {_name}")
            except AssertionError as e:
                _failed += 1
                print(f"FAIL {_name}: {e}")
    print("all tests passed" if not _failed else f"{_failed} test(s) failed")
    sys.exit(1 if _failed else 0)
