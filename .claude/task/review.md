# Review

diff_sha256: 46d2be1a2e86cbc0b7397ca30714cec8046b3ac1205ed1bcc9316c14d3bed7e6
rounds: 2

Issue #42. Round 1 on the cumulative diff (tree f01a0f5): data-engineer-reviewer,
platform-reviewer, equity-analyst-reviewer and scope-auditor PASS. Follow-ups applied: the stale
`table_index` claim in `.claude/active_work.md` corrected (the only other copy in the repo), and
the larger-table case added to `known_limits`. Round 2 on the delta (tree b144143): scope-auditor
PASS (no other reviewer's routed files changed).

equity-analyst-reviewer ran as a general-purpose agent following
`.claude/agents/equity-analyst-reviewer.md` verbatim on that role's model: the role file's
frontmatter does not parse (an unquoted `: ` in `description`), so the harness does not
register it as an agent type. Raised with the owner.

Coordinator evidence: `pytest tests` 1105 passed; context budget passes. Removing
`min_overlap=MIN_SEED_OVERLAP` from `refresh_market` fails the recorded-DAX-page test;
disabling the comparison fails the re-key and 16-of-20 boundary tests. Files restored.

## data-engineer-reviewer

VERDICT: PASS
reviewed_tree: f01a0f5bc2ca3095c96bfc81dc4b0b7903a73ad7
risks_checked:
- The overlap check runs before any write; a refusal leaves the seed byte-identical.
- The refresh script reports a refused market as failed, exits 1 and continues with others.
- Threshold inclusive; empty committed seed and duplicate tickers handled; import unchecked.
follow_ups:
- A 25-name index trips the check on 4 or more replacements (owner decision (i); watch the
  first small-index rebalance).
- A larger table containing the whole seed passes (now in `known_limits`).

## platform-reviewer

VERDICT: PASS
reviewed_tree: f01a0f5bc2ca3095c96bfc81dc4b0b7903a73ad7
risks_checked:
- Fail-closed and re-run safe; the import path never reaches the check.
- Each new test fails when its part of the change is reverted; one shared threshold constant.
- Runbook, skill and checklist claims match the code; no new dependency, CI or cost change.
follow_ups:
- `.claude/active_work.md` still called `table_index` silently wrong (applied).
- Larger-table case (now in `known_limits`).
- "85%" appears as prose beside the `MIN_SEED_OVERLAP` constant in long-lived docs.

## equity-analyst-reviewer

VERDICT: PASS
reviewed_tree: f01a0f5bc2ca3095c96bfc81dc4b0b7903a73ad7
risks_checked:
- The `docs/data_contract.md` hunk is checklist step 2 only; no metric, eligibility or
  assessment content changed.
- The `strip_suffix` instruction matches `refresh.py` and `constituent_sources.yml`.
- No finance content or advice elsewhere in the diff.

## scope-auditor

Round 1 PASS (tree f01a0f5). Round 2:

VERDICT: PASS
reviewed_tree: b144143bd0fcdaab19cc84c2d929f4d184cb5253
risks_checked:
- The corrected handover claim matches the `path.exists()` gate in `seeds.py`.
- The new known limit accurately describes the one-way overlap measure.
