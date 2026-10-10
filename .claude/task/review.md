# Review

diff_sha256: 4ef307d11b3a5fe54d1850060c7880209725d73cedf48c49ce9fb73d74b05691
rounds: 1

Issue #47, MR 1 of 2. Round 1 on the cumulative diff (tree cc8b5ca): scope-auditor, platform-reviewer
and equity-analyst-reviewer all PASS. equity-analyst-reviewer ran as a general-purpose agent
following `.claude/agents/equity-analyst-reviewer.md` verbatim on that role's model (#48).

Wording fixes applied after the PASS verdicts, no new round (the precedent in #46's review): north_star.md
"no spread among them" reworded to match `benchmark_range`'s zero-width-after-clamp case, and the same
claim in `docs/ui/card_metric_cell.md`; `docs/data_contract.md` "UI omits benchmark line" (a second
copy of the claim finding 21 changes); the metric_layer.md paragraph cut to one sentence and its
`assessment_rules.py` claim dropped; the `design_system.md` `Clear saved` smoke item (same skin claim
as finding 25); the test docstring naming the gate; the `benchmark_range` docstring now names
`PEER_THRESHOLD`; the sweep script's docstring, repo-root anchoring and self-exclusion. The two widened
docs are recorded in the contract's decisions_reserved.

Follow-ups, filed as issues after the MR opens: the Discover preset cutoffs differ from the verdict
bands (owner content, `scripts/assessment_rules.py`), and a null value passes a preset
(undocumented); `importance_tier` and `basis_column` have no frontend reader (seed column removal,
stale claims in `scripts/export_metric_definitions_json.py` and `dbt_analytics/seeds/_seeds.yml`).

Coordinator evidence: `python .claude/task/dead_code_sweep.py` prints clean, and prints the 14 expected
hits on main; every contract grep returns the stated result; `test_peer_threshold_matches_the_dbt_benchmark_gate`
fails with PEER_THRESHOLD = 9; full suite 1148 passed; `scripts/bootstrap.py --verify` passes; the
em-dash check passes.

## scope-auditor

VERDICT: PASS
reviewed_tree: cc8b5cad34937c1299af2a63c9b19c7abe0836b1
risks_checked:
- Every path in the diff is inside scope_paths; no amendment lacked authority.
- No behaviour change: `build_card_html` keeps only the old falsy-`scope_meta` path; render order is unchanged; the learn-panel string is byte-identical at PEER_THRESHOLD = 8.
- Docs match the source: north_star.md, discover_list.md, discover_header.md, design_system.md against card_ui.py, card_copy.py, brand.py, app.py and the per-metric dbt gate.
wording_fixes: all applied (see above).

## platform-reviewer

VERDICT: PASS
reviewed_tree: cc8b5cad34937c1299af2a63c9b19c7abe0836b1
risks_checked:
- No caller of a removed or changed symbol remains anywhere in the repo, including tests, scripts and docs.
- Rendering is unchanged; the pin test fails closed, its regex matches the SQL line, and CI runs it without a path filter.
- The two deleted tests asserted only the removed symbols; live `metrics_for_card` behaviour stays covered.
wording_fixes: applied.

## equity-analyst-reviewer

VERDICT: PASS
reviewed_tree: cc8b5cad34937c1299af2a63c9b19c7abe0836b1
risks_checked:
- The rewritten benchmark-unavailable behaviour matches `benchmark_range`, `_benchmark_eligible` and the per-metric dbt gate; the old false claim is gone.
- No advice language, no invented threshold, no new score or percentile claim in the touched strings.
- `METRIC_PRESETS` is read only inside `frontend/explore_filters.py`, so "only the Discover filter reads" holds.
wording_fixes: applied.
