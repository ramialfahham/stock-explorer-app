# Review

diff_sha256: dc7ed82de9f557dc58d62eaea118242515db346cf3bdcfeff48fa9323aeb8c20

Three rounds. Reviewers: scope-auditor (required by `always`) and cto-reviewer (run
voluntarily). No other reviewer is required: the staged set is one skill file, the contract, the
handover and one doc, and `.claude/review_routing.json` has no pattern matching any of them
beyond `always`.

**Reviewer dispatch:** the plugin's reviewer agent types are not registered as dispatchable in
this session, so each ran as a general-purpose agent instructed to read its own role file
verbatim first. Cold blinded input, read-only, index frozen before dispatch each round.

**Final verdicts:** scope-auditor PASS (round 3), cto-reviewer PASS (round 3).

## What this is

`.claude/skills/onboard-market/SKILL.md`, so that an agent asked to add a market finds the
activation checklist instead of improvising one. Phase 1 item 1b.

## The judgement that shaped it, and how it was wrong at first

France was onboarded by hand specifically to learn the procedure well enough to write a skill.
What that branch actually found is that the procedure was **already written down** in
`docs/data_contract.md` and simply not read. So the failure mode was discovery, not content, and
the skill's job is to make an agent find the checklist and understand what they are signing up
for, not to restate it.

**The first draft did not honour that.** It restated four checklist steps in prose while
asserting on line 11 that it did not, and the one number it restated was wrong: it attributed
the WARN-below-20 threshold to `check_eligibility_baseline.py` when it lives in
`check_pipeline_completeness.py`. **The predicted drift arrived at birth, inside the paragraph
that duplicated the step.** Both reviewers found it independently.

The file went from 900 words to 428. What survives is only what no document carries.

## The acceptance test was the root cause

The contract's criterion was "restates NO checklist step. Verified: zero numbered steps in the
file." Zero numbered steps was true. The file restated four steps anyway.

**A formatting count cannot detect duplication.** scope-auditor put it exactly: "no numbered
steps is not the same test as no second copy." The criterion is now a comparison that can
actually fail: for each mechanic the file mentions, does `docs/data_contract.md` already carry
it? If yes, cut it and point. Applied mechanically, that test removed the sector check, the
collision guidance, the acceptance gate, the two-halves rule, and step 7's mechanism.

## The fix that recreated the defect it fixed

`docs/development_workflow.md` planned a rival skill under a different name, covering the same
checklist. Left alone it would have told the next agent to build a second overlapping copy, so
it was updated to point at this one.

**The update named both traps in prose.** That made the skill's own "in no document" claim false
on merge, and created a fresh second copy in the same edit that removed one. cto-reviewer caught
it. The doc now points without naming.

## Other findings worth keeping

- **The description broke the skill's own rule.** It listed OMXS 30 for Sweden among three
  owner-chosen indices, presenting as settled an index the owner has not picked, inside a file
  whose rule is to present options and recommend rather than choose silently. Replaced with OBX.
- **A decision right was misfiled.** "Dropping a constituent" sat under "the owner's call" and
  was then decided in the next clause, contradicting the France contract's classification of the
  identical `ML.PA` question. It is an implementation judgement with a defensible default: carry
  it and let eligibility drop it.
- **An unrun result was reported as an outcome**, twice. First an extrapolated post-France deck
  size; then, after that was cut, a five-market runtime measurement phrased as if it were
  France's. France has not run.
- Smaller: the step count summed to ten against a seven-step checklist; the Haiku cost was
  overstated as "every refresh, permanently"; "nothing in the codebase inserts into it" was
  false, since migration 014 does.

## Escalated, not self-authorised

**`.claude/review_routing.json` has no `.claude/skills/*` pattern.** A skill instructs every
future agent on a task class, the same authority class as `.claude/agents/*` and
`.claude/settings.json`, both of which route to cto-reviewer. From this commit on, a file with
that reach can be added or changed with only scope-auditor required. cto-reviewer was run
voluntarily here and confirmed the gap is load-bearing rather than cosmetic, and supplied the
one-line fix (`".claude/skills/*": ["cto-reviewer"]`) for the owner to apply or decline. Editing
the routing file is a governance change and is the owner's under section 6, so it was flagged
rather than taken.

## Verification

- pytest 287, unchanged: the diff is markdown only and touches no code, data, schema, hook, CI
  file, dependency or setting.
- Both surviving traps verified genuinely undocumented, twice each and independently: `403` in
  `docs/` is only ever the Supabase Management API, and `table_index` appears only as bare config
  values with no explanation anywhere.
- Every reference the skill makes resolves: `_CURRENCY_SYMBOLS` at both cited paths and holding
  none of CAD/CHF/SEK/DKK/NOK; the currency proposal recorded as overturnable; the 2 hour CI
  timeout; the seven-step pre-France checklist confirmed against `691610b0^`.
- Zero em or en dashes on any added line.

## Left standing deliberately

The skill points at `.claude/active_work.md` for the currency proposal, which is a rolling
handover that gets rewritten. Both reviewers noted the pointer will rot and neither asked for a
change: the repo's own convention sends open items there rather than to a contract, and the
proposal is spent once the queued markets land.

## scope-auditor

Rounds 1 to 3. FAIL, FAIL, PASS.

Round 1 found the drifted threshold, the step count that summed to ten, and the rival skill plan
in `docs/development_workflow.md`. Its finding 8 was the one that mattered most and was not even
blocking: the acceptance test was a formalism that could not detect the property it named. Round
2 found the trim incomplete by that new test, and caught the description presenting an
owner-unchosen index as settled. Round 3 verified each mechanic against the checklist one final
time and confirmed the two traps genuinely absent from `docs/`.

VERDICT: PASS

## cto-reviewer

Rounds 1 to 3. FAIL, FAIL, PASS. Not required by routing; run because a skill instructs every
future agent on a task class.

Verified every factual assertion in the file against source each round, and reported the hit
rate honestly rather than only the misses. Round 1 caught the threshold misattribution
independently and located the correct owner (`check_pipeline_completeness.py:18`), and noted the
description lacked an exclusion clause in a repo where "market" is heavily overloaded. Round 2
caught the `development_workflow.md` update recreating the duplication it removed. Round 3
caught the five-market runtime being read as France's. It also confirmed the routing gap is
load-bearing and supplied the one-line fix for the owner rather than applying it.

VERDICT: PASS
