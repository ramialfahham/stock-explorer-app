"""Shared helpers for self-gating Bash hooks.

Self-gating means: the hook matcher is just "Bash" (fires on every Bash call),
and the *script* decides whether the command actually matches. This avoids the
fragile `if: Bash(pattern*)` matcher, which in practice fires on unrelated
read-only commands (e.g. `git log --grep=merge`, `cat`) -- a cry-wolf failure
that trains the agent to ignore the guardrail.

Every hook that uses these helpers must fail OPEN: on any unexpected error,
return without blocking, so a hook bug never breaks the user's workflow.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys

# The opt-in marker: every hook short-circuits on `project_opted_in()` unless
# this file exists, so a checkout without review routing sees no gate, no
# denial, and no injected context. review_routing.json is the marker because
# it's the file the review gate reads anyway.
OPT_IN_MARKER = os.path.join(".claude", "review_routing.json")

# Shell operators that separate one simple-command from the next.
_SEP = re.compile(r"\|\||&&|[;|\n]")
# Leading noise to strip before reading the command's first real token:
# env assignments (FOO=bar), and common wrappers.
_PREFIX = re.compile(r"^(?:\w+=\S*\s+|sudo\s+|command\s+|nohup\s+|time\s+|env\s+)+")


def project_root(event: dict | None = None) -> str:
    """Where the project is: CLAUDE_PROJECT_DIR (set by Claude Code for hook
    commands), else the event's `cwd`, else the process cwd."""
    return (os.environ.get("CLAUDE_PROJECT_DIR")
            or ((event or {}).get("cwd") if isinstance(event, dict) else None)
            or os.getcwd())


_LEADING_CD = re.compile(r'^cd\s+(?:"([^"]+)"|\'([^\']+)\'|(\S+))\s*(?:&&|;)')


_GIT_BASH_DRIVE = re.compile(r"^/([a-zA-Z])(?:/(.*))?$")


def native_path(path: str, base: str | None = None, windows: bool = os.name == "nt") -> str:
    """A `cd` target as this Python process can open it: `~` expanded, a Git Bash
    drive path (`/c/x`) turned into `c:/x` on Windows, and a relative path joined
    to `base` (the directory the shell was in). `$VAR` is left alone: the hook's
    environment is not the shell's, so expanding it would be a guess."""
    path = os.path.expanduser(path)
    m = _GIT_BASH_DRIVE.match(path) if windows else None
    if m:
        path = f"{m.group(1)}:/{m.group(2) or ''}"
    if base and not os.path.isabs(path):
        path = os.path.join(base, path)
    return path


def leading_cd_dir(command: str, base: str | None = None) -> str | None:
    """The directory of a literal leading `cd <dir> &&` / `cd <dir>;`, if it exists.
    The rest of such a command (e.g. `cd <worktree> && git commit`) runs there, while
    CLAUDE_PROJECT_DIR still names the main checkout. Only a leading `cd` counts."""
    m = _LEADING_CD.match((command or "").strip())
    if not m:
        return None
    raw = m.group(1) or m.group(2) or m.group(3)
    path = native_path(raw, base) if raw else None
    return path if path and os.path.isdir(path) else None


def _toplevel(path: str | None) -> str | None:
    if not path or not os.path.isdir(path):
        return None
    try:
        return subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=path, capture_output=True, text=True, timeout=10,
        ).stdout.strip() or None
    except Exception:
        return None


def command_root(command: str, event: dict | None = None) -> str:
    """The git checkout a command acts on, as its toplevel: a leading `cd` target,
    else the event's `cwd` (the Bash tool keeps its directory between calls, so a
    `cd <worktree>` in an earlier call still applies), else CLAUDE_PROJECT_DIR,
    else the process cwd. Every candidate is resolved to its toplevel, so a
    subdirectory never narrows the gate's `git diff -- .` to that subtree."""
    cwd = event.get("cwd") if isinstance(event, dict) else None
    fallback = os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
    for candidate in (leading_cd_dir(command, cwd), cwd, fallback):
        top = _toplevel(candidate)
        if top:
            return top
    return fallback


def project_opted_in(event: dict | None = None) -> bool:
    """True if the project this hook fires in has review routing
    (see OPT_IN_MARKER). Fails OPEN in the hook's sense -- any error reads as
    'not opted in', i.e. the hook does nothing."""
    try:
        return os.path.isfile(os.path.join(project_root(event), OPT_IN_MARKER))
    except Exception:
        return False


def read_event() -> dict:
    """Read and parse the hook event JSON from stdin. {} on any failure."""
    try:
        return json.loads(sys.stdin.read() or "{}")
    except Exception:
        return {}


def bash_command(event: dict) -> str:
    """Extract the Bash command string from a hook event, or ''."""
    try:
        return (event.get("tool_input") or {}).get("command") or ""
    except Exception:
        return ""


def simple_commands(command: str):
    """Yield each simple-command in a (possibly compound) shell command,
    with leading env-assignments / wrappers stripped, so callers can match
    against the actual invocation rather than substrings anywhere in the line."""
    for part in _SEP.split(command or ""):
        part = part.strip()
        if not part:
            continue
        yield _PREFIX.sub("", part).strip()


# git global options that consume the FOLLOWING token as their argument, so we
# can skip past them to find the real subcommand (e.g. `git -c k=v commit`).
_GIT_OPTS_WITH_ARG = {"-C", "-c", "--git-dir", "--work-tree", "--namespace",
                      "--super-prefix"}


_GROUP_LEAD = re.compile(r"^[({]+")
_GROUP_TRAIL = re.compile(r"[)};]+$")


def _degroup(toks: list[str]) -> list[str]:
    """Strip a single layer of subshell/brace-group punctuation stuck to the
    first and last token -- `(git commit -m x)` and `{ git commit -m x; }`
    tokenize with that punctuation attached (simple_commands splits on shell
    operators, not parens/braces, so a `&&`/`;` INSIDE a group can already
    separate `git` from its wrapper -- this only needs to handle a group with
    no such separator inside, e.g. wrapping a single command). NOT a real
    shell parser: nested or multi-command groups aren't unwrapped, so a git
    invocation buried deeper than one group level can still slip past."""
    if not toks:
        return toks
    out = list(toks)
    out[0] = _GROUP_LEAD.sub("", out[0])
    out[-1] = _GROUP_TRAIL.sub("", out[-1])
    return [t for t in out if t]


def git_subcommand(toks: list[str]) -> str | None:
    """The git subcommand in a token list, skipping global options and their
    arguments, or None if this isn't a `git` invocation. So `git log --grep
    commit` returns 'log' (not a commit) while `git -c k=v commit` returns
    'commit'. Matching the subcommand -- not a substring anywhere in the line --
    is what keeps the guards from tripping on read-only commands that merely
    contain 'commit', and from missing a commit hidden behind global options.
    Also degroups a single wrapping `(...)`/`{ ...; }` first, so `(git commit
    -m x)` isn't invisible to every guard in this repo -- see `_degroup`."""
    toks = _degroup(toks)
    if not toks or toks[0] != "git":
        return None
    i = 1
    while i < len(toks):
        tok = toks[i]
        if tok in _GIT_OPTS_WITH_ARG:
            i += 2  # option consumes the next token as its value
            continue
        if tok.startswith("-"):
            i += 1  # standalone global flag (e.g. --no-pager, --exec-path=x)
            continue
        return tok  # first non-option token is the subcommand
    return None


def is_commit_subcommand(toks: list[str]) -> bool:
    """True if `toks` is a `git commit` invocation that will actually commit.
    `--dry-run` makes no commit at all, so a guard that fires on it anyway is
    a false positive with no security value -- this was independently
    reimplemented three ways across the hooks here (one of them missing the
    `--dry-run` exemption entirely, a real bug), so it lives here once now."""
    return git_subcommand(toks) == "commit" and "--dry-run" not in toks


_HEREDOC_MARK = re.compile(r"<<-?\s*'?\"?\w+")
_QUOTED = re.compile(r"'[^']*'|\"[^\"]*\"")


def strip_quoted_and_heredoc(command: str) -> str:
    """Command text with quoted substrings removed and everything from the first
    heredoc marker truncated. Lets callers scan for shell OPERATORS (redirects,
    flags) without false-positives on quoted SQL ("x > 0.5"), commit-message
    bodies, or heredoc content."""
    try:
        cut = _HEREDOC_MARK.search(command or "")
        head = command[: cut.start()] if cut else (command or "")
        return _QUOTED.sub(" ", head)
    except Exception:
        return command or ""


def emit_context(event_name: str, text: str) -> None:
    """Inject additional context for the model (non-blocking)."""
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": event_name,
            "additionalContext": text,
        }
    }))


def emit_deny(reason: str) -> None:
    """Deny a PreToolUse tool call with a reason shown to the model."""
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    }))
