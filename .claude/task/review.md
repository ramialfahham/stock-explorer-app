# Review

diff_sha256: 1550761dd894c8c7b16d39ef51e9e425b89117cab644e0187c9d019173ec1241
rounds: 2

The AI read gets the rules' own reasons for the verdict (#65 follow-on; no verdict rule changed). Round 1
(tree 93c5b24): scope-auditor, platform-reviewer and equity-analyst-reviewer all FAIL: "the company is not
burning cash" overstated a missing runway; the reasons were not in the input hash, so a stored read could
quote a stale reason; four mutants survived the tests (the ROA dedupe, the core-only red cause, the
pre-revenue reasons, the weak core axes); a negative prompt assertion broke the done_when search; the
header and growth line differed from the wording first shown to the owner. Round 2 (tree 889ecf9, delta
only): all three PASS. Wording fixes applied after the PASS verdicts, no round 3: the green closing line
says "no falling revenue is shown" (a missing growth value counts as not falling); the hash covers only an
operating card's annual-margin flag; docs describe the new hash recipe and the no-burn note; stale
function names and hash comments repointed; a test renamed to say what it checks.
equity-analyst-reviewer's remaining follow-ups ("weak" for a guard-driven band reads as a verdict on the
cause) are declared in the contract and filed with #66.

Coordinator evidence:
- Mutation checks, file restored after each: dropping the ROA dedupe, the core-only red filter, a
  pre-revenue axis role and the reasons in the hash each fail 1 to 4 tests.
- `pytest tests` 1350 passed; `scripts/bootstrap.py --verify` passes (dbt build 149 tests); budget,
  narrative-date and em-dash checks pass. Every existing verdict test passes unchanged.
- No band, threshold or color changed. Impact check behind the #65 decision: production 1250 cards, growth
  decides 44; a growth cap would move 28 green cards to yellow; the owner chose no new rule.

follow_ups: #66 (residual guard gaps, plus the items below) and #65 (open for any later growth rule):
reword guard-driven "weak" bands; a metric absent from the numbers list can still be named; the card face's
net-cash line; `build_read_messages` takes the verdict and the row separately.

## Owner answers

CPO ANSWER: acknowledged. The owner answered "A, commit and push" to the question listing the block header,
the growth line label, the closing-line wording, "no cash burn is shown", the hash change, three extra
comment and doc files in scope and the data contract budget 67000 to 68100. No FAIL stands at round 2.
Earlier chat answers: tell the AI the real reasons (yes); no new growth rule (B). Follow-ups: #66, #65.

## scope-auditor

VERDICT: PASS
reviewed_tree: 889ecf923673723e3467d3b1caae2af5bb2ab23c
risks_checked:
- No band, threshold or color changed; every `_evaluate_*` body keeps its thresholds.
- The changed header, growth label and closing lines are disclosed and match the signed prompt bullet.
- Scope additions are comment and doc pointers.
wording_fixes: applied.

## platform-reviewer

VERDICT: PASS
reviewed_tree: 889ecf923673723e3467d3b1caae2af5bb2ab23c
risks_checked:
- The four surviving mutants are now pinned by exact-line and invariant tests.
- The hash stays deterministic and the existing hash tests still hold.
- The dead wrappers are gone and `normalize_company_type` is intact.
wording_fixes: applied.

## equity-analyst-reviewer

VERDICT: PASS
reviewed_tree: 889ecf923673723e3467d3b1caae2af5bb2ab23c
risks_checked:
- "no cash burn is shown" is accurate for every null-runway case.
- The data_contract paragraph matches the code; the remaining gaps are declared.
wording_fixes: applied.
