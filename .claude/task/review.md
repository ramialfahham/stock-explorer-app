# Review

diff_sha256: a58e0693f73dfe4280c8bcec7cbad3dc24b12a1edc1a1126b43d5d015ed20484

Nine rounds. Rounds 1-8 each returned at least one FAIL; round 9 is all PASS and is what
this hash covers. The substantive payload (one `learn` string in
`dbt_analytics/seeds/metric_catalogue.csv` plus its regenerated `frontend/metrics.json`) was
byte-stable from round 1 onward — every FAIL was against the handover and contract prose
accompanying it.

**Reviewer dispatch, recorded because it differs from previous MRs on this repo:** the
plugin's reviewer agent types (`scope-auditor`, `analytics-engineer-reviewer`,
`cto-reviewer`) and the in-repo `equity-analyst-reviewer` were not registered as dispatchable
agent types in this session's harness. Each reviewer was therefore run as a general-purpose
agent instructed to first read its own role definition file verbatim
(`~/.claude/plugins/cache/dbt-agent-kit/dbt-agent-kit/0.1.0/agents/*.md`, and
`.claude/agents/equity-analyst-reviewer.md`) and follow it for the whole task. Same role
text, same cold blinded input (`.claude/task/review_input.patch`), read-only. Flagging in
case the missing agent registration is itself worth fixing.

**Round history** (detail in `.claude/task/contract.md` `amendments`):
1. scope-auditor FAIL — handover contradicted the diff; `done_when` had silently dropped the
   handover-update requirement; authority trail did not record the proposed phrasing.
2. scope-auditor FAIL — `done_when` required three reviewers where
   `.claude/review_routing.json` requires four (`frontend/metrics.json` matches `frontend/*`
   -> cto-reviewer). The routing was NOT weakened; the reviewer was added and run.
3. cto-reviewer FAIL — handover asserted 910 live cards in five places while this branch's
   own new text said 907.
4. all PASS, but two cto-reviewer accuracy notes were fixed rather than carried.
5. scope-auditor and cto-reviewer FAIL, independently — the round-4 "fix" was itself wrong
   about what `scripts/check_eligibility_baseline.py` compares.
6. cto-reviewer FAIL — numbers right, concluding generalization still unchecked.
7. cto-reviewer and scope-auditor FAIL — the same misconception restated in a new location,
   and a causal claim that contradicted this branch's own text about the CI path.
8. all PASS after the unverified conclusions were deleted rather than corrected a fourth
   time; scope-auditor's observation that ~18 lines of gate internals had accreted in the
   handover as sediment from the review argument itself was accepted and that prose removed.
9. all PASS, plus one amendments-log honesty fix from round 8's non-blocking note.

## scope-auditor
VERDICT: PASS
risks_checked:
- All four staged paths inside `scope_paths`; no unstaged tracked edits and no prior commits,
  so the staged diff is the whole branch.
- Field-by-field parse of the seed vs HEAD: 17 rows and 21 columns both sides, exactly one
  changed field (`cash_runway_months.learn`), matching the owner-approved phrase verbatim.
- Required-reviewer set re-derived independently from `.claude/review_routing.json` rather
  than trusting `done_when`: the same four, no missing fifth.
- Repo-wide sweep for the old phrase: no other carrier; the known stale
  `docs/data_contract.md:236-237` line is MR !33's and is declared a follow-up, not narrowed out.
- Amendments log honesty: the round-6 withdrawal is now checkable against a round-5 entry
  that marks its own supersession.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- CSV column-shift risk from a hand-edited quoted field: parsed HEAD vs staged, 17 rows x 21
  columns both sides, exactly one differing field, other unicode fields byte-identical.
- Frontend-bridge no-drift lock: regenerated `frontend/metrics.json` from the staged seed via
  `scripts/export_metric_definitions_json.py`, content-identical;
  `tests/tooling/test_metric_catalogue.py` 5 passed, full suite 209 passed.
- Warehouse reach: no dbt model or macro refs `metric_catalogue`, `_seeds.yml` declares no
  test on `learn`, and `scripts/export_to_supabase.py` ships only `marts.mart_stock_cards`.
- Consumption layer computes nothing: the exporter still only selects, coerces, splits and
  sorts; `docs/engineering_standards.md` and `docs/layering.md` carry no seed rules to breach.
- Every pipeline claim in the new handover prose verified against source, including that
  `check_eligibility_baseline.py` runs only at `.gitlab-ci.yml:177` and `:255`, which is what
  makes the branch's "do not assume it watched this dip" correct.

## equity-analyst-reviewer
VERDICT: PASS
risks_checked:
- New wording against both classifier branches (`int_stock__card_metrics.sql:224-246`):
  "little or no revenue" covers `revenue <= 0` and positive-but-under-0.1%-of-market-cap,
  where "pre-revenue" was literally false for the second — a correction, not a loosening.
- Relative-threshold trap: a high-revenue company could in principle be called "little
  revenue", but that needs a price/sales above 1000x; the dataset's next-most-extreme case is
  157x short of DYL, so unreachable in this universe.
- Intra-row consistency: `applicability` ("Only for companies burning cash"), `direction`,
  `gloss` and the formula all still cohere with the new sentence; one field changed.
- Cross-row: the three "Breaks for pre-revenue firms (revenue ~= 0)" strings are on
  `operating` metrics, are not read by the frontend at all, and still describe the negligible
  case — not stale.
- Educational-not-advice: no buy/sell/hold, no price target, no second-person instruction.
- Handover financial claims: DYL's margin figures, the "~100% of span" peer-clustering
  conclusion, the "still classified `operating`" timing, and the 910/907/168 arithmetic all
  check out.

## cto-reviewer
VERDICT: PASS
risks_checked:
- Seed and generated JSON untouched since round 8; `tests/tooling/test_metric_catalogue.py`
  5/5 proves the JSON is a genuine regeneration, not a hand-edit.
- No unverified causal claim about the eligibility gate re-entered the handover: swept every
  `843` / `baseline` / `check_eligibility` mention; the note states only measured counts and
  explicitly disclaims both cause and gate coverage.
- Every line citation the branch adds re-read against source
  (`check_eligibility_baseline.py:163-199`, `:189-193`, `:200-214`, `:236-240`,
  `.gitlab-ci.yml:255` and `:259-262`, `frontend/explore_filters.py:56-57`,
  `frontend/card_copy.py:13`), including the derived 800 warn floor.
- Guard integrity: no hook, CI, dependency, lockfile or plugin-config file in the diff;
  `.claude/review_routing.json:21` independently confirms the `frontend/*` -> cto-reviewer
  routing, so the fourth reviewer is codified rather than invented.
- Patch/staged-state agreement: `review_input.patch` byte-identical to `git diff --cached`.
