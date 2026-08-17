# Review

diff_sha256: 3bee6a9cea4b2516b8f0c22e9b974accb5dd41e6c9c57b24ee8cc17c8ca9ef3a

Six rounds total. Real findings each round, all fixed and re-verified before the
next round — see `.claude/task/contract.md`'s `amendments` for the full account
of each finding and fix.

- Round 1 (scope-auditor, cto-reviewer): both FAILed —
  `frontend/row_ui.py` shipped with zero test coverage (contract had flagged
  this as a maybe and dropped it silently); scope-auditor additionally flagged
  that partial 480px smoke coverage was proceeding toward commit without
  recorded owner sign-off. Fixed: added `tests/frontend/test_row_ui.py`;
  escalated the smoke-coverage question to the owner in-thread.
- Round 2 (cto-reviewer): PASS, independently re-ran pytest and verified the
  test-coverage fix and a live DOM/CSS check.
- Round 3 (scope-auditor): FAIL — a new global button-radius CSS rule reaches
  Saved's focus view (untested), and "unchanged code" wasn't a sound rationale
  to skip re-verifying it. Also caught during this same pass, independently:
  a real CSS hover-highlight bug (bleeding to all rows instead of the one
  under the pointer) found via the owner-requested real screenshots. Fixed
  both: opened the focus view live and confirmed the button renders correctly;
  fixed the `:has()` selector to scope hover to the correct row only.
- Round 3 (cto-reviewer): PASS, verified the hover-bleed fix's CSS logic
  directly against the real DOM structure.
- Round 4 (scope-auditor): FAIL — the new `docs/ui/design_system.md` token
  table made unverified/fabricated "Used by" claims for two tokens
  (`--ss-space-1`, `--ss-space-3`) that were declared but never actually wired
  into the CSS. Fixed by wiring both into their real matching sites
  (exact-value substitutions) and correcting the doc.
- Round 5 (scope-auditor): FAIL — same defect class survived for a third
  token (`--ss-space-4`'s "page gutter" claim) because round 4's fix only
  checked the two rows it was told to fix. Fixed by wiring it in too and
  re-verifying every row in the table this time, not just the flagged ones.
- Round 6 (scope-auditor): PASS, independently re-verified all 7 token-table
  rows against a fresh grep, plus a full fresh pass on scope/decisions/routing.
- Round 3 (cto-reviewer, final): PASS, independently re-verified the three
  token-wiring substitutions are value-identical and re-checked the full diff.

## scope-auditor
VERDICT: PASS
risks_checked:
- Token table accuracy — re-ran the grep independently and hand-verified all
  7 rows against real `var()` call sites in `frontend/styles.py`; every "Used
  by" claim traces to a genuine site, including the two previously
  fabricated/unwired rows and the two never-before-checked rows
  (`--ss-radius-control`, `--ss-row-title`).
- Stale class references after the rename/deletion — grepped the entire
  worktree (not scoped to `frontend/`) for every removed/renamed class name;
  zero live references remain outside the contract's own historical prose.
- `decisions_reserved` vs. actual code — checked each of the 5 owner-approved
  items (row radius, row background, Search cap, Search interaction model,
  button-radius scope) against the diff; all implemented exactly as approved,
  nothing silently extended (no color/background reskin leaked into
  Landing/Overflow, which remain untouched).

## cto-reviewer
VERDICT: PASS
risks_checked:
- Value-identical substitution claim for the three token-wiring fixes: read
  `frontend/styles.py` directly and cross-checked each against both the old
  literal and the `:root` definition — all three are genuine zero-value-change
  swaps, not disguised behavior changes.
- Dead-CSS removal / stale-reference risk: ran the `done_when` grep, then a
  broader repo-wide pass; zero live hits. Ran the full test suite from a real
  venv (`tests/frontend/` 76 passed, full suite 145 passed).
- No new dependency, no requirements/lockfile touched, no secrets/tokens in
  the diff, no CI/hook/plugin-config touched, no cost-relevant change — matches
  the contract's own impact_map (pure frontend styling + one new small module).
