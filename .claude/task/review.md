# Review

diff_sha256: 83983fde140c1fdf4b2d447ddbb8acca110cab0f31f21eae72eb1116b0001f7e
rounds: 1

AI read, no buy/sell/price words. Round 1 (tree f2e139f): scope-auditor PASS, platform-reviewer PASS. equity-analyst-reviewer was not routed: no docs/metric_layer.md, docs/data_contract.md or catalogue file changed.

Wording fixes applied after the PASS verdicts, no second round (the precedent in #46's review): the new bullet says "revenue" for every company and "sales" only for an operating company (a financial company's metric glosses say revenue is "not sales"); the prompt's own margin rule no longer says "units the company sells"; the test derives its word list from the guard's regex and checks each word is in the bullet (the author ran the mutation of dropping "sells" from the bullet and the test fails), is renamed to say "bare" words and has no date; the guard comment no longer states a fact the rejected reads contradict; three handover claims corrected (hashed inputs, "sells" or "selling", the first-run date). Open, not built: the owner-signed prompt still uses the barred words in its own instructions (buy, sell, price) and in the advice rule, because the guard checks model output only; the model names what a company sells although it is given only numbers (the prompt forbids outside facts; no guard checks it).

Coordinator evidence: full suite 1161 passed; `scripts/bootstrap.py --verify` passes; the em-dash check passes; `INPUT_HASH_VERSION` unchanged.

## Owner answers

CPO ANSWER: recorded for the no-sell-words rule (no issue; found in the 2026-10-11 production run, 13 of 223 new reads rejected on "sells" or "selling"). The owner was shown the finding and the proposed prompt rule in plain words and answered "sells rule yes".

## scope-auditor

VERDICT: PASS
reviewed_tree: f2e139f33a4e0369c28b33bf35cc38b29044f500
risks_checked:
- The diff stays inside scope_paths; the guard, INPUT_HASH_VERSION and the frontend are unchanged, so no regeneration is forced.
- The handover paragraph is internally consistent and states state, not narrative.
- No doc lists the guard's banned words or contradicts the new rule.
wording_fixes: applied.

## platform-reviewer

VERDICT: PASS
reviewed_tree: f2e139f33a4e0369c28b33bf35cc38b29044f500
risks_checked:
- The new bullet collides with no other prompt rule and no metric label or gloss carries a banned word, so it can be followed.
- The test fails when the bullet is removed; the guard's regex is exactly the seven listed words.
- Nothing else changed.
wording_fixes: applied.
