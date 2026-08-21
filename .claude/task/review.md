# Review

diff_sha256: c4e2111a871acd157b74e596d119fe9c5fbbd020946a49b31973ed344df6b84a

Three rounds, four required reviewers (scope-auditor always; cto-reviewer per
`frontend/*`/`tests/*`; equity-analyst-reviewer per `*metric_catalogue.csv`;
analytics-engineer-reviewer per the routing file's separate, broader bare `*.csv` pattern,
which also matches this same seed file — both rules fire independently, same standing
decision this repo made before to honor a literal broad pattern rather than treat its scope
as a routing bug). Real findings in rounds 1 and 2, all fixed; round 3 clean across all four
— analytics-engineer-reviewer was only run once the commit gate caught it as missing, but
its hunt was against the same final, already-passing hash, so it stands as this task's one
and only round for that reviewer.

- Round 1: scope-auditor PASS. cto-reviewer FAIL — three findings: `render_learn_panel()`'s
  docstring in `frontend/card_ui.py` still listed "about-this-company" as panel content, a
  recurrence of the exact split-docstring defect this same role caught on these same two
  functions in the prior task; `docs/north_star.md`'s "Company context" paragraph still said
  the full description "lives in the card's one learn panel... not its own separate toggle,"
  contradicting the diff's own Deep-tier table update three lines below; `disclosure_html()`'s
  new falsy-skippable `preview` behavior — the only genuinely new logic in this diff — had no
  test anywhere asserting it. equity-analyst-reviewer FAIL — two findings: the owner-approved
  "Option A" copy for `ebit_margin_pct` dropped the word "divide," describing the calculation
  as summing two numbers without stating the division that makes the result a margin (not
  part of what was approved — an unflagged accuracy regression riding along with the approved
  opening-sentence fix); the contract's `decisions_reserved` never quoted the approved text
  verbatim, so there was nothing to check byte-for-byte against. All fixed: docstring
  corrected; a fuller sweep of `north_star.md` (prompted by finding the first stale spot) also
  caught a second, separate paragraph describing per-metric text as always-visible without a
  toggle — fixed in the same pass; a new test added to `tests/frontend/test_disclosure_html.py`
  (confirmed to fail against a reconstruction of the pre-fix `disclosure_html()`); the "divide"
  fix applied directly (a factual completion, not a new framing decision — confirmed with the
  owner in conversation that this class of fix doesn't need the same two-option process as the
  original phrasing question) and the approved text quoted verbatim in the contract.
- Round 2: scope-auditor PASS. cto-reviewer FAIL — one finding: the contract's
  `technical_definition` cited a nonexistent test file (`tests/tooling/test_metric_definitions.py`)
  as the metrics.json no-drift lock; the real file is `tests/tooling/test_metric_catalogue.py`.
  equity-analyst-reviewer FAIL — one finding: the "divide" fix's own grammar was ambiguous —
  "summed across the last four quarters" read, by ordinary proximity parsing, as modifying only
  "Total Revenue," leaving Operating Income's period unstated; a beginner reading literally
  could compute roughly a quarter of the true margin. Both fixed: citation corrected; "both"
  added so the modifier explicitly binds to both terms — applied directly, same reasoning as
  the round-1 copy fix (factual/clarity completion, not new framing).
- Round 3: all three reviewers PASS, each independently re-verifying every round-1/2 finding
  against live file content — re-running the no-drift test directly, re-reading the corrected
  docstring and docs fresh, hashing the contract's quoted text against the seed and
  `metrics.json` rather than trusting the narrative, reconstructing the pre-fix
  `disclosure_html()` to confirm the new test actually guards something. No new findings.

## scope-auditor
VERDICT: PASS
risks_checked:
- Citation fix verified directly: `tests/tooling/test_metric_catalogue.py` exists and its
  `test_regenerated_json_matches_committed()` regenerates and diffs against the committed
  `frontend/metrics.json`, exactly as the contract claims.
- Grammar fix verified fresh: "both summed across the last four quarters" unambiguously binds
  to both Operating Income and Total Revenue on a read with no memory of the prior draft.

## cto-reviewer
VERDICT: PASS
risks_checked:
- Citation fix is a real, functioning guard, not a name-only correction — ran the test
  directly, then independently reproduced the same regen+diff outside pytest.
- Full suite green (167 passed); the 27 directly relevant tests re-run individually by name.
- `ebit_margin_pct` text agrees byte-for-byte across the seed, `metrics.json`, and the
  contract's quote, including the em dash at the same byte offset.
- Round-3 edit confined to exactly the claimed 3 files, confirmed via file mtimes.
- No dangling references to any round-1/2-removed symbol anywhere in the repo.
- Existing `disclosure_html()` caller (`saved_news.py`) structurally unaffected by the new
  falsy-preview branch — its own `is_truncated()` guard means `preview` is never empty there.

## equity-analyst-reviewer
VERDICT: PASS
risks_checked:
- Grammar/ambiguity of "both" — reread fresh, no alternate antecedent survives; the
  proximity ambiguity round 2 found is resolved.
- Byte-exact match across contract quote, seed, and `metrics.json` — SHA-256 hashed all
  three independently, identical.
- Row internal consistency — every other field on the `ebit_margin_pct` row (calculation,
  numerator/denominator expressions, applicability, etc.) unchanged and still consistent
  with the new `learn` text; cross-checked the "both summed across four quarters" claim
  against the row's own four-quarter numerator/denominator expressions — factually accurate.
- No orphaned copy of the superseded text anywhere in tests, fixtures, or other docs.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- Layer placement — diffed all 21 seed columns field-by-field; only `learn` changed, no
  formula/mapping/eligibility column touched.
- CSV structural integrity — ran `dbt seed --full-refresh` and `dbt test` live against the
  edited seed (clean), plus the Python-side catalogue test suite (5/5), confirming the
  long multi-clause quoted field didn't misalign any column.
- Seed-to-frontend no-drift lock executed live (not assumed) — regenerated `metrics.json`
  from the staged seed via the real export script and confirmed byte-identical to committed.
- Traced reach into the dbt DAG directly — the seed has no `ref()` path into any
  staging/base/core/intermediate/marts model; the seed-to-model link is a text-scan test,
  not a SQL join, so this change cannot reach computed metric values or the Supabase export.
