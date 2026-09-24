"""Tests for _command_utils, shared by both hard guards (commit_review_gate,
branch_discipline): git-subcommand detection, `cd` target resolution
(native_path, leading_cd_dir) and the checkout a command acts on (command_root).

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
    command_root,
    git_subcommand,
    is_commit_subcommand,
    leading_cd_dir,
    native_path,
    simple_commands,
)


def _same(a, b):
    return os.path.normcase(os.path.realpath(a)) == os.path.normcase(os.path.realpath(b))


def test_git_bash_drive_paths_become_windows_paths():
    assert native_path("/c/Users/x/wt", windows=True) == "c:/Users/x/wt"
    assert native_path("/D", windows=True) == "D:/"
    assert native_path("/c/Users/x/wt", windows=False) == "/c/Users/x/wt"
    assert native_path("/usr/local", windows=True) == "/usr/local"


def test_leading_cd_follows_a_git_bash_spelled_path():
    with tempfile.TemporaryDirectory() as d:
        real = os.path.realpath(d)
        if os.name != "nt" or real[1] != ":":
            return
        bash = "/" + real[0].lower() + "/" + real[3:].replace("\\", "/")
        assert _same(leading_cd_dir(f"cd {bash} && git commit -m x"), real)


def test_leading_cd_expands_home_and_joins_relative_paths():
    with tempfile.TemporaryDirectory() as home:
        os.makedirs(os.path.join(home, "wt", "sub"))
        saved = {k: os.environ.get(k) for k in ("HOME", "USERPROFILE")}
        os.environ["HOME"] = os.environ["USERPROFILE"] = home
        try:
            assert _same(leading_cd_dir("cd ~/wt && git commit -m x"), os.path.join(home, "wt"))
        finally:
            for k, v in saved.items():
                if v is None:
                    os.environ.pop(k, None)
                else:
                    os.environ[k] = v
        base = os.path.join(home, "wt")
        assert _same(leading_cd_dir("cd sub && git commit -m x", base), os.path.join(base, "sub"))


def test_command_root_resolves_a_relative_cd_from_the_event_cwd():
    # the relative target is joined to the event's cwd, not the hook process's cwd
    with tempfile.TemporaryDirectory() as parent:
        subprocess.run(["git", "init", "-q", parent], check=True)
        nested = os.path.join(parent, "wt")
        subprocess.run(["git", "init", "-q", nested], check=True)
        root = command_root("cd wt && git commit -m x", {"cwd": parent})
        assert _same(root, nested)


def test_command_root_resolves_a_subdirectory_cwd_to_the_toplevel():
    # a subdirectory root would narrow the gate's `git diff -- .` to that subtree
    with tempfile.TemporaryDirectory() as repo:
        subprocess.run(["git", "init", "-q", repo], check=True)
        sub = os.path.join(repo, "a", "b")
        os.makedirs(sub)
        top = os.path.normcase(os.path.realpath(repo))
        assert os.path.normcase(os.path.realpath(command_root("ls", {"cwd": sub}))) == top
        assert os.path.normcase(os.path.realpath(command_root(f'cd "{sub}" && ls'))) == top


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
