# Review

diff_sha256: 877c6341adca9a18c568bff194154c293cc9125db12a564d7410419b84066c79

No formal task contract for this change — a small, fully-specified docs-only trim: remove the
Apple-specific example (`"Apple's real card, current ratio 0.89, FCF margin 23.7%, is exactly
this case"`) from `docs/data_contract.md`'s "Joint liquidity evaluation, operating only" bullet,
applying the same standing rule established earlier this session for code comments (no concrete
real-world examples baked into permanent text) to the matching docs example. Two reviewers
required per `.claude/review_routing.json`: `scope-auditor` (always), `equity-analyst-reviewer`
(`docs/data_contract.md`).

## scope-auditor
Two rounds. Round 1 (diff hash
`0171b6b8d8596ee184e286411c51a46e0fc40a85209afd54bbf83f5b4bdcf8e7`): **FAIL** -- the edit also
reworded an adjacent independent clause ("so a company with excellent free cash flow but a
merely-weak current ratio was capped at yellow regardless of how strong its cash generation was"
became "so strong free cash flow could never rescue a merely-weak current ratio"), dropping
"capped at yellow," the exact idiom used identically two bullets earlier and one bullet later in
the same list -- exceeding the stated scope of a one-clause removal.

Fixed: restored the original wording verbatim, removing only the Apple parenthetical.

Round 2 (diff hash `877c6341adca9a18c568bff194154c293cc9125db12a564d7410419b84066c79`):
VERDICT: PASS
risks_checked:
- Confirmed via `git diff --word-diff=plain HEAD` that the only content-level change is the Apple
  clause removed (`6/8; Apple's real card, current ratio 0.89, FCF margin 23.7%, is exactly this
  case).` -> `6/8).`); every other word in the bullet is byte-identical, and the line-level diff
  is pure markdown rewrap from the paragraph now being one line shorter.
- The "capped at yellow" idiom family elsewhere in the doc (`yellow-capping ceiling`,
  `capping at yellow`) is untouched -- neither line appears in the diff at all.
- No em/en-dash on the added line (`6/8).`, plain ASCII).
- Only `docs/data_contract.md` is staged; `.gh-issue-body.md` and `.venv/` are pre-existing
  untracked artifacts, not part of this diff.

## equity-analyst-reviewer
VERDICT: PASS
risks_checked:
- Cross-checked the remaining prose against `scripts/assessment_rules.py`
  (`_current_ratio_axis_with_fcf_coverage_relief`, `CURRENT_RATIO_WEAK_TH`/`CURRENT_RATIO_GOOD_TH`/
  `CURRENT_RATIO_LIQUIDITY_FLOOR`) -- every remaining claim matches the code exactly (dollar
  comparison not margin-based, the 0.5 floor as a hard cutoff, relief landing on `ok` never
  `good`, scoped to `current_ratio_stmt` only). The mechanism description is complete and accurate
  without the Apple example.
- No information loss: the removed figures (current ratio 0.89, FCF margin 23.7%) remain
  documented at their source, `docs/backlog/gemini_verdict_feedback.md`'s point 6 entry, which the
  bullet's retained citation (`points 6/8`) still points to -- this is a de-duplication of an
  already-sourced fact, not a loss of a claim that only existed here.
- No advice-line, direction-correctness, or beginner-jargon issues -- internal assessment-rule
  documentation, not user-facing card copy.
