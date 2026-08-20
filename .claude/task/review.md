# Review

diff_sha256: 27c14806833d216680a85948f17107fb6efe382299ced92d3fe910ec5f3b50e6

Two rounds. Round 1 found real issues (one owner-authority gap, two design/hygiene
findings); all three resolved and recorded in `.claude/task/contract.md`'s `amendments`
before round 2. Round 2 independently re-verified each fix against the actual diff — not
taken on faith — and both required reviewers PASS.

- Round 1 (scope-auditor): FAIL — `frontend/card_copy.py`'s `MEDIAN_PRIMER` string had its
  arrow-glyph legend clause ("↑ higher than median · ↓ lower than median · → at median")
  removed during implementation with no recorded owner authority; only
  `_BENCHMARK_INDICATOR_LABELS` was named as pre-approved copy in `explicitly_not_in_scope`.
  Escalated to the owner: keep the fix (the legend described arrows the card no longer
  shows) vs. revert. Owner chose to keep it; recorded as an amendment.
- Round 1 (cto-reviewer): FAIL — two findings. (1) This diff removes the last production
  caller of the arrow-glyph `benchmark_indicator()`/`_BENCHMARK_INDICATORS`
  (`frontend/card_copy.py`), leaving them dead; the only remaining reference is
  `tests/frontend/test_benchmark_indicators.py`, outside this contract's `scope_paths`.
  (2) `VERDICT_MEANING` (duplicated into `frontend/card_copy.py` with a new
  `tests/tooling/` sync-guard test, per the original plan) had zero consumers anywhere in
  the diff. Both escalated to the owner: (1) fold cleanup into this diff (widen scope_paths)
  vs. keep deferred to the already-spawned follow-up task; (2) keep the unused mechanism
  as insurance vs. drop it (YAGNI). Owner chose: keep (1) deferred — not fixed here, tracked
  separately; drop (2) — `VERDICT_MEANING` and `tests/tooling/test_card_copy_verdict_sync.py`
  removed from the diff entirely. Both recorded as amendments.
- Round 2 (scope-auditor): PASS — independently verified all three round-1 fixes against
  the actual diff and the actual `amendments` text (not the round-1 narrative alone), then
  ran a full fresh hunt: scope (14 changed files, all inside `scope_paths`), doc-sync across
  all four touched docs, join-key consistency between `fetch_card_assessments` and
  `attach_assessments`, and a preview/full-text equivalence boundary case for short
  (non-truncated) company summaries.
- Round 2 (cto-reviewer): PASS — independently confirmed `VERDICT_MEANING` and its guard
  test are genuinely absent (grep across the full repo, not just the diff) and that the one
  remaining `VERDICT_MEANING` hit is an unrelated, out-of-scope doc describing a different
  future MR on the pipeline side. Re-verified re-run/interruption safety for the three new
  Supabase-read functions, dead-CSS removal (grepped every removed class name repo-wide),
  the `show_metric_school` → `show_learn_panel` rename's three call sites, and cost impact
  (no change to fetch frequency/volume).

## scope-auditor
VERDICT: PASS
risks_checked:
- Round-1's MEDIAN_PRIMER fix — read the actual diff hunk and the actual amendments-section
  text side by side; they match exactly, and the owner authority is genuinely recorded in
  `contract.md`, not merely claimed.
- VERDICT_MEANING removal — grepped the full diff and current worktree for the symbol;
  confirmed absent from `frontend/`, confirmed the backend's independent copy in
  `scripts/assessment_rules.py` is untouched and non-conflicting (separate deploy target).
- File-level scope — enumerated all 14 `diff --git` headers against `scope_paths` line by
  line; no file outside scope, including confirming `frontend/metric_school.py`'s
  conditional inclusion was correctly left unused.
- Company-description preview/full equivalence for short summaries — traced
  `truncate_words()` to confirm the diff's switch from `full` to `preview` text in
  `_company_summary_html` causes no content loss for non-truncated cards.

## cto-reviewer
VERDICT: PASS
risks_checked:
- VERDICT_MEANING removal claim (round-1 FAIL driver) — verified by reading the full
  `card_copy.py`, confirming `tests/tooling/test_card_copy_verdict_sync.py` is absent from
  the filesystem, and repo-wide grep showing zero remaining `.py` references.
- Dead-CSS removal correctness — grepped the whole repo (not just the diff) for every
  removed class name (`ss-company-about*`, `ss-learn-panel*`, `ss-company-summary-preview`,
  `ss-company-summary--empty`) to confirm none are still referenced by any Python file
  before trusting the removal; all confirmed orphaned.
- Join-key consistency between `fetch_card_assessments`'s dict keys and
  `attach_assessments`'s `_card_key` lookup, and that `attach_assessments` doesn't mutate
  its input — read both implementations directly and cross-checked against the paired
  tests.
