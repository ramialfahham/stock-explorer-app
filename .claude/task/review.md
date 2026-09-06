# Review

diff_sha256: 2d7c5b7060ec185d1f1057fda8e621516ccf567d901fa6a5294b521b3157e492

## scope-auditor
Round 1 FAILED (single finding)
- `.claude/active_work.md` -- listed in `scope_paths`, required by `done_when` ("item 3 closed
  out"), correctly edited in the working tree, but not staged (`git status --short` showed
  ` M`, `git diff --staged --stat` for this path was empty). Reasoning: committing without it
  leaves the backlog item looking open in git history.

Resolution: `active_work.md`'s own "Review mechanics" note states the historical two-commit
split is "no longer load-bearing... committing it alongside the change it describes works fine
too." Took that documented option: `git add .claude/active_work.md`. Confirmed genuinely
resolved, not just asserted, via a narrow round-2 re-check (below) rather than self-certifying,
since the additional wording-fix rounds since round 1 also touched `active_work.md` and
`contract.md` again and a fresh independent check was warranted regardless.

Round 2 (narrow re-check of the staging resolution, plus scope_paths/done_when accuracy after
the later wording-fix rounds -- nothing else in scope):
VERDICT: PASS
risks_checked:
- `.claude/active_work.md` genuinely staged, not just claimed: confirmed via `git diff --staged
  --name-only`/`--stat`; an empty unstaged `git diff` ruled out any working-tree/index
  divergence.
- `scope_paths` in `contract.md` vs. `git diff --staged --name-only`: exact 8-file match, no
  undisclosed scope creep from the round-2/round-3 wording-fix edits.
- `done_when`'s "item 3 closed out": `active_work.md`'s item 3 heading and body reflect the
  final, corrected state (heading fixed from "bank card's" to "financial-type card's", final
  sentence quoted, marked "fixed").
- `active_work.md`'s quoted caveat sentence vs. `frontend/card_copy.py`'s
  `FINANCIAL_CAPITAL_ADEQUACY_CAVEAT` constant: byte-level comparison, character-for-character
  identical (84 bytes, plain ASCII).
- No em/en dash on any staged added line, repo-wide, for this diff.

## cto-reviewer
VERDICT: PASS
risks_checked:
- `_health_block_html`'s new caveat branch: traced all three narrative states (ai_read present,
  absent-with-fallback, absent-with-no-fallback) -- caveat_html is computed once from
  `company_type` before the branch and appended in all three return paths, confirmed by reading
  the diff directly rather than trusting the description.
- Read `READ_SYSTEM_PROMPT` in `scripts/assessment_rules.py` directly -- confirmed it is a style
  instruction to the model, not a schema-enforced/validated field, so the deterministic
  card-face caveat is not redundant with something CI already guarantees.
- Confirmed `FINANCIAL_CAPITAL_ADEQUACY_CAVEAT`'s exact text matches what the owner approved
  verbatim in-thread, and that it contains no apostrophe or em/en dash (would break `_esc()`
  literal-substring test matching, per the constraint `VERDICT_FALLBACK_READ`'s own comment
  already documents). Checked against the round-1 wording, before equity-analyst-reviewer's two
  content rounds below changed the exact string twice more -- unaffected, since this check was
  of the render mechanism (branch structure, apostrophe/dash constraint), not the financial
  content, and neither the mechanism nor the constraint changed across any wording round.
- Full `pytest` suite: transient 3-failed/515-passed on first run, diagnosed as stale
  `__pycache__` bytecode (not a real defect) -- cleared pycache, reran twice, 518 passed both
  times.
- Non-blocking observation: `.claude/active_work.md` unstaged at time of review -- read as
  consistent with the session's documented two-commit convention, not a defect. (Superseded by
  the resolution above -- it is staged in the commit this review now describes.)

## equity-analyst-reviewer
Round 1 FAILED (two findings)
- `frontend/card_copy.py` (`FINANCIAL_CAPITAL_ADEQUACY_CAVEAT`) -- "this bank" is factually
  wrong for the render gate it's tied to: `company_type == "financial"` is the whole GICS
  "Financial Services" sector (`docs/data_contract.md`'s classification note), not depository
  banks. Confirmed against this app's own live S&P 500 constituent data: Visa, Mastercard,
  BlackRock, Moody's, S&P Global, CME Group, ICE, Chubb, Progressive, Allstate, Aon, Marsh
  McLennan, American Express, and Berkshire Hathaway all resolve `company_type = "financial"`
  and none are banks. Regresses from `scripts/assessment_rules.py`'s own already-shipped,
  already-reviewed `READ_SYSTEM_PROMPT` wording ("this financial company's balance-sheet safety
  or capital strength"), which a prior review already corrected away from this exact
  bank-specific over-reach.
- Same constant -- "profitability only" is imprecise: `revenue_growth_yoy_pct` also renders on
  financial-type cards (`applies_to = operating|financial` in `metric_catalogue.csv`, catalogued
  under `growth`, not `profitability`).

Both findings independently verified (not taken on trust) by reading `docs/data_contract.md`,
`scripts/assessment_rules.py`, `metric_catalogue.csv`, and the live constituent seed data
directly. Taken back to the owner per §6 (user-visible wording is an owner call) rather than
self-corrected -- owner approved a fix mirroring the already-reviewed `READ_SYSTEM_PROMPT`
framing. Full trail in `contract.md`'s amendments.

Round 2 FAILED (narrow re-check of the round-1 fix, nothing else in scope)
- Confirmed round-1 finding 1 (the bank-specific claim) genuinely fixed: "this company" makes
  no sector-specific claim, correctly generalized.
- Round-1 finding 2 only partially fixed: independently re-queried `metric_catalogue.csv` and
  confirmed financial-type cards render 4 metrics across 3 `perspective` values (`profitability`:
  `net_margin_pct`; `returns`: `statement_roe_pct`, `roa_pct`; `growth`:
  `revenue_growth_yoy_pct`) -- "profitability and returns only" still omitted the growth metric,
  same defect category as round 1, narrower (1-of-3 missing instead of 2-of-3). No new defect
  from the wording change itself (no apostrophe/dash, grammar clean, no advice-like language).

Round 3 FAILED (narrow re-check of the invariant-fix wording, nothing else in scope)
- The sentence itself passed clean, first clean pass in three rounds: makes no claim about card
  contents (states only an absence, so immune to future `metric_catalogue.csv` drift);
  independently confirmed its one claim -- capital adequacy is never assessed -- holds
  unconditionally (no metric for any `company_type` measures CET1/Tier 1 or bank-style capital
  adequacy; the closest general-leverage metrics, `debt_to_equity` and `net_debt_to_ebitda`, are
  both `applies_to = operating` only, explicitly marked meaningless for financials); no
  apostrophe/em-dash/en-dash (checked character by character); "this company" reads naturally
  against the established pattern elsewhere in the file and the card's own header context.
- But caught two staleness bugs elsewhere in the same staged diff, same defect class this review
  exists to catch (a stale/wrong caveat quote): `.claude/active_work.md` still quoted the
  round-1 wording ("this bank... profitability only"), and `contract.md`'s amendments hadn't yet
  recorded round-3's approval trail. Both fixed: `active_work.md`'s item 3 now quotes the actual
  shipped sentence and its heading corrected from "bank card's" to "financial-type card's";
  `contract.md` amendments now records the full round-2/round-3 trail including the owner
  approval for this exact sentence. Confirmed documentation lag from iterating the wording
  twice more after the round-2 record was written, not a missing approval -- no further
  re-dispatch: these were file-freshness fixes, not a subjective judgment the reviewer needs to
  re-render on.

Round 4 (narrow re-check of the two round-3 doc-staleness fixes only):
VERDICT: PASS
risks_checked:
- `active_work.md` item 3 quotes the sentence that actually matches `frontend/card_copy.py`'s
  live constant character-for-character, confirmed via direct comparison; heading corrected to
  "financial-type card's"; the only remaining "this bank" / incomplete-enumeration text in the
  file is inside explicit historical framing describing superseded wording, not presented as
  current.
- `contract.md`'s amendments carry a verifiable trail for both prior rounds (what was wrong,
  the evidence, the fix, and that the owner approved it) rather than a bare "approved" assertion.
- No new defect on the changed lines: zero em/en-dash unicode characters in either file, no
  apostrophe in either transcription of the caveat sentence, cross-checked against `contract.md`
  and the actual code layout for factual consistency.

## Full suite
518 passed after every round: initial implementation, pycache-clear rerun (twice), the
company_type-gate mutation-test restore, the round-1 wording fix, and the round-3 wording fix.
Test assertions reference `FINANCIAL_CAPITAL_ADEQUACY_CAVEAT` by symbol, not a hardcoded string,
so no test edits were needed across any wording round.

## Mutation test
Backed up `frontend/card_ui.py`, removed the `company_type == "financial"` gate in
`_health_block_html` (caveat rendered unconditionally), reran the 3 new tests --
`test_health_block_omits_capital_adequacy_caveat_on_non_financial_cards` failed as expected
(both `operating`/`pre_revenue` sub-cases). Restored the file, reran full suite: 518 passed.

## Manual verification
Running dev server, checked against the final wording:
- "Admiral Group" (ADM, Financial Services, a car/home insurer -- not a bank, the exact scenario
  round-1's finding was about) shows "These numbers do not show whether this company holds
  enough capital to stay safe." under the AI-written narrative.
- "3i" (III, Financial Services, a private equity firm -- also not a bank) shows the same
  caveat, alongside its own Growth-perspective metric (Rev growth YoY) rendered on the same
  card, confirming the final wording's no-enumeration approach doesn't contradict what's
  actually shown.
- "3M" (MMM, Industrials, operating-type) shows no caveat at all.
