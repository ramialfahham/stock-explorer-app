# Review

diff_sha256: 52be73cb33da41d70779581e4ec015ab22d5c66e23862d116be853b173aafd56
rounds: 3

AI read, facts and not the verdict. Round 1 (tree 087629c): all three FAIL (an unsatisfiable done_when grep; a contradiction check that false-blocks a red read calling one metric healthy and could raise recurring API cost; a not-green rule that did not fit the verdict functions). Round 2 (tree e02d295): equity-analyst-reviewer PASS, platform-reviewer PASS, scope-auditor FAIL (a false retry sentence in data_contract.md; the owner-signed not-green wording had changed without an owner answer). Round 3 (tree ba2c860, the cap): all three PASS. equity-analyst-reviewer ran as a general-purpose agent following `.claude/agents/equity-analyst-reviewer.md` verbatim on that role's model (#48).

Wording fixes applied after the round-3 PASS verdicts, no fourth round (the precedent in #46's review): the red-cause list now also appears in the test docstring, three assertions pin the red figure list and the yellow clause, a stale sentence in the `generate_assessments.py` header (a base record also carries an explicit clear for a stale read), and two known limits recorded in the contract (the type-agnostic red list; "a measure could not be worked out" can be misapplied). Open follow-ups, not built: a check that ties the visible text to the verdict (new mechanism, owner); the `data_contract.md` list of causes of an absent `ai_read` omits the verdict-meaning and malformed-payload rejects; the `generate_assessments` rejection path has no mutation test for the `verdict_meaning_violation` call site.

Coordinator evidence: full suite 1160 passed; `scripts/bootstrap.py --verify` passes; the em-dash check passes; the contract greps return nothing; `INPUT_HASH_VERSION` unchanged and now pinned by a test.

## Owner answers

CPO ANSWER: recorded for the AI-read change (no issue; raised by the owner from two card screenshots). (a) The owner chose "1 gradual" and saw hand-written example texts, then said "go". (b) The signed not-green sentence named falling revenue as an example cause, which the verdict rules never produce for red. The owner was asked in plain words whether to use the corrected wording (A) or keep the signed one (B) and answered "A". (c) Dropping the text-vs-verdict contradiction check, which would false-block a red read and could raise recurring API calls, was decided by the agent under the owner's earlier delegation ("act as the expert"); a check that ties the text to the verdict stays an open owner decision in the contract's known_limits.

## scope-auditor

VERDICT: PASS
reviewed_tree: ba2c86055b416ae2c294ced68195769727564548
risks_checked:
- The false retry sentence is fixed against `_clear_stale_read_if_present` and `attach_reads`.
- The owner's answer A and the final prompt wording are recorded; no hash or version change and no new rejection trigger, so no added API calls.
- Every pinned prompt phrase in the tests matches the prompt text.

## platform-reviewer

VERDICT: PASS
reviewed_tree: ba2c86055b416ae2c294ced68195769727564548
risks_checked:
- The prompt-structure tests still match the edited prompt; the new phrases trip no advice or style regex.
- Formatting limited to the two-blank-line trim; the docstring edit matches the function.
- `INPUT_HASH_VERSION` unchanged and pinned.

## equity-analyst-reviewer

VERDICT: PASS
reviewed_tree: ba2c86055b416ae2c294ced68195769727564548
risks_checked:
- The not-green sentence is accurate against the verdict functions for operating, financial and pre-revenue; falling revenue is never named as the cause of red.
- No advice, invented threshold or outside fact; the numeric guard still covers every cited number.
- Residual risk without a text-vs-verdict check is acceptable for a gradual rollout and is stated truthfully.
