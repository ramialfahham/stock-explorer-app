# Review

diff_sha256: 9a2b7c0a7bbce427b652137e9ed4535c62ed3e40e89b24d5ad49152dbe425294
rounds: 3

Grounded AI read (owner-reported live bug). Round 1 (tree ded58fc): scope-auditor, platform-reviewer
and equity-analyst-reviewer all FAIL: a currency check that rejected "100 SEK", a fraction check
that rejected "the third quarter", a false "net cash" line for negative EBITDA, thin glosses with the
rule "explain only with the Meaning line", and handover items removed. Round 2 (tree cbd1734): equity
and platform PASS, scope FAIL (hyphenated fractions slipped through; the Meaning lines differed from
the card without recorded owner authority; a budget figure; two open items dropped from the handover).
Round 3 (tree cb5bf11, the cap): equity and platform PASS, scope FAIL on two regex defects of the
round-3 delta (a lookbehind on the euro, pound and yen signs let "C€" through; "the second-half of
the year" was rejected). Both are fixed in code with tests, along with the auditor's wording fixes
and the platform reviewer's boundary tests; that last delta was not re-reviewed, because the cap
allows no round 4. The owner picks the exit below.

Coordinator evidence: `pytest tests` 1334 passed; `scripts/bootstrap.py --verify` passes (dbt build
149 tests); budget, narrative-date and em-dash checks pass. The rejection rate of the new checks is
unknown until the production run (zero extra spend); it is counted from the job log afterwards.

follow_ups: filed as issue #66 (residual guard gaps; the net-cash line on the card face; sector
medians; catalogue audit against ISO/IEC 11179-4) and #65 (verdict: growth plays almost no role).

## Owner answers

CPO ANSWER: commit what is proven and file the rest. The owner answered "commit and push it" to the
round-3 exit question; the remaining scope-auditor FAIL (two regex defects, fixed with tests after the
verdict and not re-reviewed because of the cap) and the other leftovers go to follow-up issue #66.
Earlier chat answers: the AI feature stays; digits for figures; regenerate every read once;
deterministic rejection with no retry; the catalogue is the only source of meaning; the three writing
standards; the prompt wording as shown; the one Meaning difference from the card (answer A); growth
keeps its direction cue; budget 67000.

## scope-auditor

VERDICT: FAIL
reviewed_tree: cb5bf116e8e41628b0b1b08e778576d24e2e19c1
risks_checked:
- Round-2 items (fractions with a hyphen, the Meaning parity, the budget, the handover items) confirmed resolved.
- Two defects in the regex the delta changed: euro, pound and yen signs without an amount passed after the lookbehind; hyphenated "second-half", "last-half", "latter-half" time phrases were rejected.
wording_fixes: applied. Both defects fixed after the verdict, with tests; not re-reviewed (cap).

## platform-reviewer

VERDICT: PASS
reviewed_tree: cb5bf116e8e41628b0b1b08e778576d24e2e19c1
risks_checked:
- Fraction and currency regexes traced against every contract example; lookbehinds are fixed width.
- Growth cue restored and the parity test equals the card for every field; one remaining difference, pinned.
- Newline test now pins the split; budgets fit.
wording_fixes: applied.

## equity-analyst-reviewer

VERDICT: PASS
reviewed_tree: cb5bf116e8e41628b0b1b08e778576d24e2e19c1
risks_checked:
- The restored growth cue does not contradict the rule that growth never explains the verdict; both are pinned by tests.
- The data-contract paragraph matches the code, with one difference from the card gloss.
wording_fixes: applied.
