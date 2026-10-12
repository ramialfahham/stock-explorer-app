# Review

diff_sha256: 2d99faf9eff99f6ffef0ee4b3c972a1be88b330c1ce3bcb87c22086a1a02a9a3
rounds: 3

AI read: revised prompt, 30-word check, one retry. The on-demand production run of 2026-10-11 accepted
0 of 353 reads (87% had a sentence over 25 words). Round 1 (tree 87408bc): scope-auditor FAIL (retries
sat outside `--max-reads`; the run budget was an owner number), platform-reviewer FAIL (only the figures
guard was tested for the retry), equity-analyst-reviewer PASS. Round 2 (tree dff40e1): equity and platform
PASS, scope ESCALATE (three owner questions). Round 3 (tree 8c95e81, the cap): all three PASS. Applied
after the PASS verdicts, no round 4: the citation validator refuses a label that is not text (an unhashable
list raised TypeError and would have aborted the whole run; one test, mutation-checked), the data contract
names `referenced_metrics` and `verdict_meaning` as the wrong-typed fields, and the contract states the full-run
size (about 1240 reads), the formulas and the basis of $5.70. That last delta was not re-reviewed (cap).

Coordinator evidence:
- Real calls, nothing written, key from the owner's `.env`: prompt versions on 60 cards (current wording 60%
  accepted at 30 words, revised wording 83%); the shipped change through the real `_generate_read` with its retry
  on 44 cards (31 operating, 11 financial, 2 pre-revenue; 25 non-USD): 44 of 44 accepted, 5 retries of a budget of 37;
  a reworded example on the same 44 cards: 39 of 44, 14 retries, so the shipped example stays (#67).
- Mutation checks, file restored after each: each of the four refusal returns flipped to "not refused", an error
  return flipped to "refused", retry disabled, budget not decremented, retry on any non-accepted read each fail 1 to
  9 tests; removing the label type check fails one test.
- `pytest tests` 1374 passed; `scripts/bootstrap.py --verify` passes (dbt build 149 tests); budget, narrative-date
  and em-dash checks pass.

follow_ups: #67 (prompt-wording items for the owner), #66 (guard gaps); before the full run, watch wall-clock time
(about 116 of 120 minutes at the retry cap).

## Owner answers

CPO ANSWER: acknowledged. The owner's chat answers: run a real-call test with the key in `.env` ("A, key is in
.env"); the retry ("B", after the cost table); start the build ("go"); retry cap 30% of reads + 20 ("A", over
40% + 20); retries count inside `--max-reads` ("A"); test a reworded example ("B"), with the rule that the shipped
example stays if acceptance falls (it fell from 44/44 to 39/44). Prompt wording items: #67. No FAIL stands.

## scope-auditor

VERDICT: PASS
reviewed_tree: 8c95e810b068813dd5abd9494a292f61bf999a06
risks_checked:
- The three owner answers are recorded; every touched file is in scope_paths; no verdict, seed, frontend, export or dbt change.
- Retry arithmetic, the `--max-reads` wording and the stale-claim greps hold.
wording_fixes: applied.

## platform-reviewer

VERDICT: PASS
reviewed_tree: 8c95e810b068813dd5abd9494a292f61bf999a06
risks_checked:
- The integer retry budget equals the old one for every read count; tests pin 20, 38 and 392.
- The retry docstring matches `_attempt_read`; the prompt is untouched.
wording_fixes: applied.

## equity-analyst-reviewer

VERDICT: PASS
reviewed_tree: 8c95e810b068813dd5abd9494a292f61bf999a06
risks_checked:
- The data contract's retry paragraph matches the code; the prompt and worked example are unchanged.
- The unsupported-claim classes are declared and sampled after the run.
wording_fixes: applied.
