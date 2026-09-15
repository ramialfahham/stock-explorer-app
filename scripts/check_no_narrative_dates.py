"""Fail when a comment, docstring, or DURABLE doc carries a date, an MR/PR reference, or
"owner-approved"/"owner decision" wording -- narrative-history language that belongs in a
commit message or MR description, not in the thing it describes (working-agreement.md §2;
engineering_standards.md §1.2/§1.3).

Scanned: every `.py`/`.sql` file's comments and docstrings, including `supabase/migrations/`
-- a migration can be edited after it first merges (confirmed in this repo's own history), so
it is not exempt (not code or string-literal data -- a Python docstring is found via `ast`, a
SQL comment via a quote-aware `--`/`/* */` scan, so a dated test fixture value or a SQL `comment
on column` string is never mistaken for a code comment); every Markdown file whose first 10
lines declare a `> DURABLE.` header, outside fenced code blocks. A `DISPOSABLE` file (the
handover, task contract/review) or an undeclared doc (the dated handover archives) is out of
scope by construction -- those are the sanctioned, point-in-time home for this content.
Open/planned work with its own narrative lives in GitLab Issues instead, per
working-agreement.md §2 -- outside this checker's file-scanning reach entirely, not an
exemption it grants.

Escape hatch for the rare case a rule needs to quote its own anti-pattern (engineering_standards.md
quoting "not 'fixed in MR !115'" as an example): a `narrative-check: allow` marker
(`# narrative-check: allow`, `-- narrative-check: allow`, `<!-- narrative-check: allow -->`)
exempts the line it's on for a `#`/`--` comment or a Markdown line; for a Python docstring or a
SQL block comment, which are checked as one unit, it exempts the whole comment/docstring.

Usage (from repo root):
    python scripts/check_no_narrative_dates.py
"""

from __future__ import annotations

import ast
import re
import sys
import tokenize
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

EXCLUDE_DIR_PARTS = {
    ".venv", "venv", ".git", "dbt_packages", "target", "node_modules", "__pycache__",
}

DATE_RE = re.compile(r"\b\d{4}-\d{2}-\d{2}\b")
MR_PR_RE = re.compile(r"\b(?:MR|PR)\s*[!#]\d+\b")
OWNER_DECISION_RE = re.compile(r"\bowner[- ](?:approved|decision)\b", re.IGNORECASE)
ALLOW_MARKER = "narrative-check: allow"
DURABLE_HEADER_RE = re.compile(r"^>\s*DURABLE\.")


def _violation_kind(text: str) -> str | None:
    if ALLOW_MARKER in text:
        return None
    if DATE_RE.search(text):
        return "date-stamp"
    if MR_PR_RE.search(text):
        return "MR/PR reference"
    if OWNER_DECISION_RE.search(text):
        return "owner-approved/owner-decision wording"
    return None


def _iter_repo_files(root: Path, suffix: str) -> list[Path]:
    out = []
    for p in root.rglob(f"*{suffix}"):
        if any(part in EXCLUDE_DIR_PARTS for part in p.parts):
            continue
        out.append(p)
    return sorted(out)


def _python_violations(path: Path) -> list[str]:
    violations = []
    try:
        source = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return violations

    try:
        tree = ast.parse(source, filename=str(path))
    except SyntaxError:
        tree = None

    if tree is not None:
        docstring_nodes = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
                body = getattr(node, "body", None)
                if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant):
                    if isinstance(body[0].value.value, str):
                        docstring_nodes.append(body[0])
        for node in docstring_nodes:
            text = ast.get_docstring(node) if hasattr(node, "body") else None
            text = node.value.value if text is None else text
            kind = _violation_kind(text)
            if kind:
                violations.append(f"{path}:{node.lineno}: {kind} in docstring")

    try:
        tokens = tokenize.generate_tokens(iter(source.splitlines(keepends=True)).__next__)
        for tok in tokens:
            if tok.type == tokenize.COMMENT:
                kind = _violation_kind(tok.string)
                if kind:
                    violations.append(f"{path}:{tok.start[0]}: {kind} in comment")
    except (tokenize.TokenError, IndentationError):
        pass

    return violations


def _sql_comment_spans(line: str) -> list[str]:
    """Return the comment portion(s) of a SQL line, skipping `--` inside a single-quoted
    string. Block comments (`/* */`) are handled separately across the whole file."""
    spans = []
    in_string = False
    i = 0
    while i < len(line):
        ch = line[i]
        if ch == "'" and not in_string:
            in_string = True
        elif ch == "'" and in_string:
            in_string = False
        elif not in_string and line[i:i + 2] == "--":
            spans.append(line[i:])
            break
        i += 1
    return spans


def _sql_violations(path: Path) -> list[str]:
    violations = []
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return violations

    for block in re.finditer(r"/\*.*?\*/", text, re.DOTALL):
        kind = _violation_kind(block.group(0))
        if kind:
            lineno = text.count("\n", 0, block.start()) + 1
            violations.append(f"{path}:{lineno}: {kind} in block comment")

    for lineno, line in enumerate(text.splitlines(), start=1):
        for span in _sql_comment_spans(line):
            kind = _violation_kind(span)
            if kind:
                violations.append(f"{path}:{lineno}: {kind} in comment")

    return violations


def _is_durable_markdown(path: Path) -> bool:
    # docs/ui/*.md uses its own "**Scope:**"/"**Authority:**" header convention instead of
    # "> DURABLE.", but check_context_budget.py already governs the whole directory at the
    # same tier as CLAUDE.md and docs/*.md -- treated as always in-scope here for the same
    # reason, rather than trying to also detect that second header shape.
    if path.parent.name == "ui" and path.parent.parent.name == "docs":
        return True
    try:
        with path.open(encoding="utf-8") as f:
            for _ in range(10):
                line = f.readline()
                if not line:
                    break
                if DURABLE_HEADER_RE.match(line.strip()):
                    return True
    except UnicodeDecodeError:
        return False
    return False


def _markdown_violations(path: Path) -> list[str]:
    if not _is_durable_markdown(path):
        return []

    violations = []
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return violations

    in_fence = False
    for lineno, line in enumerate(text.splitlines(), start=1):
        if line.strip().startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        kind = _violation_kind(line)
        if kind:
            violations.append(f"{path}:{lineno}: {kind}")

    return violations


def find_violations(root: Path) -> list[str]:
    violations: list[str] = []
    for path in _iter_repo_files(root, ".py"):
        violations.extend(v.replace(str(root) + "\\", "").replace(str(root) + "/", "")
                           for v in _python_violations(path))
    for path in _iter_repo_files(root, ".sql"):
        violations.extend(v.replace(str(root) + "\\", "").replace(str(root) + "/", "")
                           for v in _sql_violations(path))
    for path in _iter_repo_files(root, ".md"):
        violations.extend(v.replace(str(root) + "\\", "").replace(str(root) + "/", "")
                           for v in _markdown_violations(path))
    return sorted(violations)


def main() -> int:
    violations = find_violations(REPO_ROOT)
    if violations:
        print("Narrative-date check FAILED:")
        for line in violations:
            print(f"  {line}")
        print(
            "\nA comment/docstring/DURABLE doc states what is true now; git records when and "
            "who (working-agreement.md §2, engineering_standards.md §1.2/§1.3). Remove the "
            "date/MR-reference/owner-decision wording, or mark a genuine exception with a "
            "trailing 'narrative-check: allow' comment."
        )
        return 1
    print("Narrative-date check passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
