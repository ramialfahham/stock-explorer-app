# Review

> DISPOSABLE. **Owns:** THIS task's reviewer verdicts and the staged-diff hash they were
> given against.
> **Never:** a rule. Overwritten by the next task.

diff_sha256: 0bf6ac16168574e7dc94f192c92e2b242bc1ccdb6a24d8deaa7d4f8182a1c0e6

Three reviewers, by routing: scope-auditor (`always`), cto-reviewer (`scripts/*`, `tests/*`),
equity-analyst-reviewer (`docs/data_contract.md`). Two rounds on this branch, on top of two
rounds already passed before this work was parked to let MR !149 (the upsert-clobbering fix)
ship first.

## What shipped

`--max-reads` caps how many NEW Claude calls `generate_assessments.py`'s AI-read step makes
per run (unbounded by default). `attach_reads()` fills cards with no stored read before cards
that only need a refresh; whatever the cap doesn't reach, or whose call fails, has any stale
stored read explicitly cleared (`_clear_stale_read_if_present()`) rather than left showing
under this run's fresh verdict and numbers. CLI validation rejects a negative value; the
function itself clamps defensively too.

This work was designed and reviewed to completion (two rounds, all reviewers passed) on a
separate branch, then stashed to let a more urgent discovery -- MR !149's upsert-clobbering
bug -- get fixed and merged first. It has now been git-stash-applied onto current main
(post-!149): the code and tests auto-merged with no textual conflicts; `docs/data_contract.md`
and `.claude/task/contract.md` had real conflicts, resolved by hand.

735 tests (was 726 after !149; net +9 for the full --max-reads feature across both review
passes).

## Rounds 1-2 (before parking, on the original branch)

Already covered in that branch's history: scope-auditor caught nothing; cto-reviewer caught a
negative-`--max-reads` slicing bug (fixed with a CLI guard + defensive clamp); equity-analyst-
reviewer caught the stale-read-masking issue that became `_clear_stale_read_if_present()`, plus
a wording overclaim and a fairness caveat that needed documenting. All resolved before parking.

## Round 1 (this branch, post-merge)

scope-auditor: PASS -- confirmed both !149's and this task's content survived the manual
merge in `docs/data_contract.md` and `.claude/task/contract.md` without either being dropped.

cto-reviewer: FAIL. The one composition path between the two features that neither task's own
review had covered -- a `_clear_stale_read_if_present()`-nulled (capped/failed) record sharing
an `_upsert_records()` call with a genuinely generated record -- had no pinning test. Fixed:
`test_a_capped_cards_cleared_read_and_a_generated_cards_fresh_read_both_survive_the_same_upsert_call`
proves they land in the same call and neither clobbers the other.

equity-analyst-reviewer: FAIL, three findings. `docs/data_contract.md`'s "ai_read absent"
causes list implied a capped card is as rare as the other four (API failure, hallucination
reject, etc.) when it's actually the expected, by-design outcome once a real cap is set --
fixed with an explicit distinction. "This step" had no antecedent -- fixed to "The AI-read
step". (Minor, not separately re-expanded: some trimmed wording, judged adequate after the
other two fixes.) Trimming to fit the file's context budget after these additions pushed it
over; `docs/context_budget.yml`'s `docs/data_contract.md` entry raised 59500 -> 60000, per
that file's own documented process for exactly this situation.

## Round 2 (this branch)

scope-auditor: PASS. cto-reviewer: PASS -- independently confirmed the new composition test
would fail against either a partial-null bug or a grouping-key regression, not just against
the new code's own internal behavior. equity-analyst-reviewer: FAIL -- a cross-reference
elsewhere in the same doc section ("a different case from the four below") wasn't updated when
the causes list grew to five. Fixed: "the five below".

## Round 3 (this branch)

equity-analyst-reviewer: PASS -- confirmed the fix, swept the rest of the file for the same
count, and independently verified a capped card genuinely belongs in the five-item group (its
verdict/snapshot_date are still written fresh every run; only ai_read/read_model are cleared).

## scope-auditor

VERDICT: PASS

## cto-reviewer

VERDICT: PASS

## equity-analyst-reviewer

VERDICT: PASS

## Owner decisions

Resume `--max-reads` now rather than wait 2 weeks for the next scheduled run to re-measure
cost first -- the cap's own correctness doesn't depend on that measurement. Owner's call, in
chat, 2026-09-15.
