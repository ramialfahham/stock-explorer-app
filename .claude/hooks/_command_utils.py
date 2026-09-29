"""Shared helpers for this repo's hooks: the self-gating Claude-side hooks on the Bash
and PowerShell tools, and the review gate's git-hook mode.

Self-gating means: the hook matcher is just the tool name (fires on every call),
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


def git_toplevel(path: str | None = None) -> str | None:
    """The toplevel of the git checkout containing `path` (default: the process cwd),
    or None outside one. A git hook runs in the checkout git is acting on, so this is
    the checkout a commit or push really touches, however the command was written."""
    try:
        return subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=path or os.getcwd(), capture_output=True, text=True, timeout=10,
        ).stdout.strip() or None
    except Exception:
        return None


def from_claude_code() -> bool:
    """True when this process descends from Claude Code: its Bash and PowerShell tools
    set CLAUDECODE=1. The review gate's git hook gates only the agent's commits, not the owner's."""
    return os.environ.get("CLAUDECODE") == "1"


# A bash heredoc body (`<<'EOF' ... EOF`) or a PowerShell here-string (`@'...'@`,
# `@"..."@`): message text, never a command, and free to contain apostrophes.
_HEREDOC_BODY = re.compile(r"<<-?\s*(['\"]?)(\w+)\1.*?\n\s*\2\b", re.DOTALL)
_HERE_STRING = re.compile(r"@(['\"])\r?\n.*?\r?\n\1@", re.DOTALL)
# The value after git's `-c`, quoted or not: `-c "core.hooksPath=x"` must stay readable.
_GIT_C_VALUE = re.compile(r"(\s-c\s+)(['\"])([^'\"]*)\2")
_EDGE_PUNCTUATION = "(){};&"
# Short commit flags whose value may be attached (`-mfix`, `-uno`): letters after one of
# these are its value, not more flags.
_COMMIT_FLAGS_TAKING_VALUE = set("mFcCtSu")
_SHORT_FLAG_WORD = re.compile(r"-[a-zA-Z]+")
# git config actions that read or remove a key rather than set it.
_CONFIG_READ_OR_UNSET = {"--get", "--get-all", "--get-regexp", "--list", "-l", "--unset",
                         "--unset-all", "--show-origin", "get", "unset"}


def _sets_hooks_path(words: list[str]) -> bool:
    """True when a `git config` command sets core.hooksPath: the key is followed by a value
    and no read or unset action is given (`git config core.hooksPath` alone only reads)."""
    lowered = [w.lower() for w in words]
    if "core.hookspath" not in lowered or _CONFIG_READ_OR_UNSET.intersection(lowered):
        return False
    return lowered.index("core.hookspath") < len(lowered) - 1


# pre-commit's SKIP or Claude Code's CLAUDECODE: an assignment (`X=`, `$env:X =`, also a
# PowerShell variable of that name), any PowerShell env-drive reference (`Env:X`, `Env:\X`,
# `$env:X`), `-u X` or `unset X`; never the bare word (a folder named `claudecode`, "skip").
_ENV_SWITCH = re.compile(
    r"(?<![\w-])((?:SKIP|CLAUDECODE)\s*=|Env:\\?(?:SKIP|CLAUDECODE)(?![\w-])"
    r"|(?:-u|unset)\s+(?:SKIP|CLAUDECODE)(?![\w-]))", re.IGNORECASE)
# The same names quoted as the argument of a PowerShell set/remove call:
# `SetEnvironmentVariable('CLAUDECODE', ...)`, `Remove-Item "Env:\CLAUDECODE"`,
# `Set-Item -Path 'Env:SKIP'`. Only a quoted string that IS the name counts, right after
# such a call, so a commit message that mentions one never does.
_ENV_NAME = re.compile(r"(?:Env:\\?)?(SKIP|CLAUDECODE)", re.IGNORECASE)
_ENV_SETTER_BEFORE = re.compile(
    r"(?:SetEnvironmentVariable\(\s*|(?:Remove-Item|Set-Item|Clear-Item|New-Item)\s+(?:-\w+\s+)*)$",
    re.IGNORECASE)


def _quoted_env_switch(text: str) -> str | None:
    """SKIP or CLAUDECODE when a top-level quoted string is exactly that name (optionally
    `Env:`-prefixed) and directly follows a call that sets or removes it; else None."""
    for m in _QUOTED.finditer(text):
        name = _ENV_NAME.fullmatch(m.group(0)[1:-1])
        if name and _ENV_SETTER_BEFORE.search(text[: m.start()]):
            return name.group(1)
    return None


def _short_flags_skip_hooks(word: str) -> bool:
    """True for a short-flag bundle on `git commit` that contains `-n` (`-n`, `-nm`, `-qn`),
    reading letters after a value-taking flag as its value (`-mfinal`, `-uno` are not)."""
    if not _SHORT_FLAG_WORD.fullmatch(word):
        return False
    for letter in word[1:]:
        if letter in _COMMIT_FLAGS_TAKING_VALUE:
            return False
        if letter == "n":
            return True
    return False


def _git_words(part: str) -> list[str]:
    """The words of one simple command from its first `git` on (so `if ($?) { git commit`
    and `& git.exe push` are read as git), with edge punctuation (`}` `)` `;`) removed and an
    unquoted `git.exe` path read as `git`; [] when the part runs no git."""
    words = [w.strip(_EDGE_PUNCTUATION) for w in part.split()]
    for i, word in enumerate(words):
        if word.replace("\\", "/").rsplit("/", 1)[-1].lower() in ("git", "git.exe"):
            return ["git", *[w for w in words[i + 1:] if w]]
    return []


def hook_bypass(command: str) -> str | None:
    """The usual spellings of skipping git's commit hooks, or None: on a command that
    commits, any `--no-v...` word (wider than git's own prefix rule on purpose), a
    short-flag bundle with `n` (`-n`, `-nm`), `core.hooksPath`, pre-commit's `SKIP` or
    CLAUDECODE (the review gate's switch) being set or unset; and setting
    `git config core.hooksPath` on its own. Pushes run no git hook here (GitLab protects `main`), so they are not scanned.
    Heredoc and here-string bodies and quoted text are ignored, except a `-c` value and a
    quoted env name passed to a PowerShell set/remove call, so a message that mentions a
    flag or a name is not a bypass. It catches accidents, not a command
    written to evade it; the MR review and GitLab's branch protection are the backstop."""
    text = _HEREDOC_BODY.sub(" ", command or "")
    text = _HERE_STRING.sub('""', text)
    quoted_switch = _quoted_env_switch(text)
    text = _GIT_C_VALUE.sub(lambda m: m.group(1) + m.group(3), text)
    text = _QUOTED.sub('""', text)
    commits = False
    for part in simple_commands(text):
        words = _git_words(part)
        sub = git_subcommand(words)
        if sub == "config" and _sets_hooks_path(words):
            return "`core.hooksPath`"
        if not is_commit_subcommand(words):
            continue
        commits = True
        for word in words:
            if word.startswith("--no-v"):
                return "`--no-verify`"
            if _short_flags_skip_hooks(word):
                return "`-n`"
        if "core.hookspath" in part.lower():
            return "`core.hooksPath`"
    if commits:
        m = _ENV_SWITCH.search(text)
        name = m.group(1) if m else quoted_switch
        if name:
            return "`CLAUDECODE`" if "CLAUDECODE" in name.upper() else "`SKIP`"
    return None


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
    """Command text with each quoted substring and PowerShell here-string replaced by an
    empty `""` and everything from the first heredoc marker truncated. Lets callers scan
    for shell OPERATORS (redirects, flags) without false-positives on quoted SQL
    ("x > 0.5"), commit-message bodies, or heredoc content."""
    try:
        text = _HERE_STRING.sub('""', command or "")
        cut = _HEREDOC_MARK.search(text)
        head = text[: cut.start()] if cut else text
        # `""` in place, not a space: a quoted value keeps its slot (`-m "msg" file.py`
        # keeps `file.py` visible as a pathspec) and stays glued to its word
        # (`user.name="A B"` stays one word).
        return _QUOTED.sub('""', head)
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
