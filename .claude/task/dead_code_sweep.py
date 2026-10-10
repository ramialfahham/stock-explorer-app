"""Task evidence for #47: dead code in frontend/. Exits 1 on any hit.

Checks, per frontend/*.py: (1) imports never used in the module, (2) top-level names that no
non-test file references (KEEP_NAMES exempts the names tests read), (3) defaulted parameters
never read in the body, or never passed by a non-test call site when the function has one
(KEEP_PARAMS exempts adjustable defaults). A reference is any identifier token in a non-test
file's text, so a mention in a comment, docstring or string counts; a name reused in an
unrelated module counts too.
"""

import ast
import os
import re
import sys
from collections import Counter
from pathlib import Path

KEEP_NAMES = {"ALL_METRICS", "_BY_ID"}
KEEP_PARAMS = {
    ("business_summary_is_truncated", "max_words"),
    ("business_summary_preview", "max_words"),
    ("headline_item_html", "max_words"),
    ("normalize_nav_page", "fallback"),
    ("disclosure_html", "wrap_class"),
    ("disclosure_html", "details_class"),
}
SKIP_DIRS = {".venv", "venv", ".git", "node_modules"}

os.chdir(Path(__file__).resolve().parents[2])
SELF = Path(__file__).resolve().relative_to(Path.cwd())
files = [p for p in Path(".").rglob("*.py") if not (set(p.parts) & SKIP_DIRS) and p != SELF]
texts = {p: p.read_text(encoding="utf-8") for p in files}
trees = {p: ast.parse(t) for p, t in texts.items()}
words = {p: Counter(re.findall(r"[A-Za-z_][A-Za-z0-9_]*", t)) for p, t in texts.items()}
frontend = sorted(Path("frontend").glob("*.py"))
if not frontend:
    sys.exit("no frontend/*.py found")
hits: list[str] = []

for p in frontend:
    imported: dict[str, int] = {}
    for node in ast.walk(trees[p]):
        if isinstance(node, ast.Import):
            for a in node.names:
                imported[(a.asname or a.name).split(".")[0]] = node.lineno
        elif isinstance(node, ast.ImportFrom) and node.module != "__future__":
            for a in node.names:
                imported[a.asname or a.name] = node.lineno
    used = {n.id for n in ast.walk(trees[p]) if isinstance(n, ast.Name)}
    for name, line in imported.items():
        if name not in used:
            hits.append(f"{p}:{line} unused import {name}")

for p in frontend:
    for node in trees[p].body:
        defined: list[str] = []
        if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
            defined = [node.name]
        elif isinstance(node, ast.Assign):
            defined = [t.id for t in node.targets if isinstance(t, ast.Name)]
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            defined = [node.target.id]
        for name in defined:
            if name.startswith("__") or name in KEEP_NAMES:
                continue
            own_refs = words[p][name] - 1
            other_prod = sum(
                words[q][name] for q in words if q != p and not str(q).startswith("tests")
            )
            if own_refs <= 0 and other_prod == 0:
                hits.append(f"{p}:{node.lineno} no production reference: {name}")

calls: dict[str, list[ast.Call]] = {}
for q, t in trees.items():
    if str(q).startswith("tests"):
        continue
    for n in ast.walk(t):
        if isinstance(n, ast.Call):
            f = n.func
            key = f.id if isinstance(f, ast.Name) else f.attr if isinstance(f, ast.Attribute) else None
            if key:
                calls.setdefault(key, []).append(n)

for p in frontend:
    for fn in ast.walk(trees[p]):
        if not isinstance(fn, ast.FunctionDef):
            continue
        a = fn.args
        positional = [x.arg for x in a.posonlyargs + a.args]
        defaulted = positional[len(positional) - len(a.defaults):] if a.defaults else []
        defaulted += [x.arg for x, d in zip(a.kwonlyargs, a.kw_defaults) if d is not None]
        for param in defaulted:
            if (fn.name, param) in KEEP_PARAMS:
                continue
            read = any(isinstance(n, ast.Name) and n.id == param for n in ast.walk(fn))
            if not read:
                hits.append(f"{p}:{fn.lineno} {fn.name}({param}) is never read")
                continue
            idx = positional.index(param) if param in positional else None
            passed = any(
                any(k.arg == param or k.arg is None for k in c.keywords)
                or (idx is not None and len(c.args) > idx)
                or any(isinstance(x, ast.Starred) for x in c.args)
                for c in calls.get(fn.name, [])
            )
            if calls.get(fn.name) and not passed:
                hits.append(f"{p}:{fn.lineno} {fn.name}({param}) is never passed by any caller")

print("\n".join(hits) if hits else "clean")
sys.exit(1 if hits else 0)
