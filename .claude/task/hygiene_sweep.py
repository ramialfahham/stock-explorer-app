"""Task evidence for #50: repo hygiene. Exits 1 on any hit.

Rules (each prints its own hits):
  R1 copies   -- no two non-test modules define a top-level function with the same body, or the
                 same name (KEEP_* exempt the pairs and names that are different jobs).
  R2 scripts  -- every scripts/*.py is imported by another script, or named by a file that is
                 not a script (CI, hook config, doc, test, ingestion, dbt). A mention inside
                 another script's text, the task folder or the handover does not count.
  R3 seeds    -- every folder under storage/seeds is a market_code in docs/market_registry.yml.
  R4 pins     -- no package is pinned (==) in two requirements/CI places.
  R5 github   -- no non-test Python code uses a GITHUB_* name (KEEP_GITHUB exempts a file).
  R6 names    -- the removed names appear nowhere outside the task folder.
"""

import ast
import hashlib
import os
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

KEEP_SAME_BODY = {frozenset({"governed_files", "governed_docs"})}
KEEP_GITHUB = {"scripts/apply_supabase_migrations.py"}
# Different jobs behind one name: the gate's _card_key and _has_business_summary read mart
# columns only, the app's also read a raw yfinance field and keep raw key types.
KEEP_SAME_NAME = {
    "main",
    "find_violations",
    "render",
    "_load_mart_rows",
    "_cell",
    "_summarize",
    "_card_key",
    "_has_business_summary",
}
SKIP_PARTS = {".venv", "venv", ".git", "node_modules", "__pycache__"}
REMOVED_NAMES = [
    "_load_active_markets",
    "_registry_active_codes",
    "_append_github_summary",
    "GITHUB_STEP_SUMMARY",
    "deduped_eligible",
    "deduped eligible",
    "deduped card-eligible",
    "jp_nikkei225_starter",
    "probe_roa_total_assets",
    "probe_quarterly_op_labels",
]
REMOVED_WORDS = ["_esc", "_sql_model_names"]
REMOVED_IN_SCOPE = [("dedupe_to_latest_snapshot", ("scripts/", "tests/tooling/"))]
NOT_A_REFERENCE = (".claude/task/", ".claude/active_work.md", "docs/quality_criteria.json")

os.chdir(Path(__file__).resolve().parents[2])
tracked = sorted(
    p
    for p in subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.split("\n")
    if p and Path(p).is_file()
)
texts: dict[str, str] = {}
for rel in tracked:
    try:
        texts[rel] = Path(rel).read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        continue
hits: list[str] = []


def non_test_py() -> list[str]:
    return [
        p
        for p in texts
        if p.endswith(".py")
        and not (set(Path(p).parts) & SKIP_PARTS)
        and Path(p).parts[0] not in ("tests", ".claude")
    ]


by_body: dict[str, list[tuple[str, str]]] = defaultdict(list)
by_name: dict[str, set[str]] = defaultdict(set)
for p in non_test_py():
    for node in ast.parse(texts[p]).body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            body = ast.dump(ast.Module(body=node.body, type_ignores=[]), annotate_fields=False)
            by_body[hashlib.md5(body.encode()).hexdigest()].append((p, node.name))
            by_name[node.name].add(p)
for group in by_body.values():
    if len({f for f, _ in group}) > 1 and frozenset(n for _, n in group) not in KEEP_SAME_BODY:
        hits.append("R1 same body: " + ", ".join(f"{f}:{n}" for f, n in group))
for name, files in sorted(by_name.items()):
    if len(files) > 1 and name not in KEEP_SAME_NAME:
        hits.append(f"R1 same name {name}: " + ", ".join(sorted(files)))

scripts = sorted(p for p in texts if re.fullmatch(r"scripts/[^/]+\.py", p))
imported_by_script: set[str] = set()
for s in scripts:
    for node in ast.walk(ast.parse(texts[s])):
        if isinstance(node, ast.Import):
            imported_by_script.update(a.name.split(".")[0] for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_by_script.add(node.module.split(".")[0])
for s in scripts:
    stem = Path(s).stem
    pattern = re.compile(rf"(?<![A-Za-z0-9_]){re.escape(stem)}(?![A-Za-z0-9_])")
    named_by = sorted(
        p
        for p, t in texts.items()
        if p not in scripts and not p.startswith(NOT_A_REFERENCE) and pattern.search(t)
    )
    if stem not in imported_by_script and not named_by:
        hits.append(f"R2 unused script: {s}")

registry = texts.get("docs/market_registry.yml", "")
codes = set(re.findall(r"^\s*-?\s*market_code:\s*(\S+)", registry, flags=re.M))
if not codes:
    sys.exit("no market_code found in docs/market_registry.yml")
seeds_root = Path("storage/seeds")
for d in sorted(seeds_root.iterdir()) if seeds_root.is_dir() else []:
    if d.is_dir() and d.name not in codes:
        hits.append(f"R3 seed folder not in registry: {d.as_posix()}")


def pins_in_requirements(rel: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for line in texts.get(rel, "").splitlines():
        m = re.match(r"\s*([A-Za-z0-9_.\-]+)(\[[^\]]*\])?==", line)
        if m:
            out[re.sub(r"[-_.]+", "-", m.group(1).lower())] = line.strip()
    return out


pin_places: dict[str, list[str]] = defaultdict(list)
for rel in sorted(p for p in texts if re.fullmatch(r"(.*/)?requirements[^/]*\.txt", p)):
    for pkg in pins_in_requirements(rel):
        pin_places[pkg].append(rel)
for rel in (".gitlab-ci.yml", "render.yaml"):
    for m in re.finditer(r"pip install\s+\"?([A-Za-z0-9_.\-]+)==", texts.get(rel, "")):
        pin_places[re.sub(r"[-_.]+", "-", m.group(1).lower())].append(rel)
for pkg, places in sorted(pin_places.items()):
    if len(places) > 1:
        hits.append(f"R4 pin repeated: {pkg} in {places}")

for p in non_test_py():
    if p in KEEP_GITHUB:
        continue
    for node in ast.walk(ast.parse(texts[p])):
        if (
            isinstance(node, ast.Constant)
            and isinstance(node.value, str)
            and re.search(r"GITHUB_[A-Z_]+", node.value)
        ):
            hits.append(f"R5 GITHUB name in code: {p}:{node.lineno}")

for p, t in texts.items():
    if p.startswith(".claude/task/"):
        continue
    for name in REMOVED_NAMES:
        if name in t:
            hits.append(f"R6 removed name {name!r} still in {p}")
    for name in REMOVED_WORDS:
        if re.search(rf"(?<![A-Za-z0-9_]){re.escape(name)}(?![A-Za-z0-9_])", t):
            hits.append(f"R6 removed name {name!r} still in {p}")
    for name, prefixes in REMOVED_IN_SCOPE:
        if p.startswith(prefixes) and name in t:
            hits.append(f"R6 removed name {name!r} still in {p}")

for h in hits:
    print(h)
print(f"hygiene_sweep: {len(hits)} hit(s)")
sys.exit(1 if hits else 0)
