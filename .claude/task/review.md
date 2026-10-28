# Review

diff_sha256: e572e50b407d197ecb43cb55795be0aefe76addf2d134973b2e5d2086d7bdc42
rounds: 1

Works #82 (FE-3 defect 17, FE-2 defect 18, FE-1 defect 21 of the second audit re-run). `DECK_COLUMNS` gains
`net_margin_pct` so the High margin pill filters financial cards (owner answer A); the stylesheet loses the rules and the
custom property nothing uses, and a test now fails on any new one; `format_snapshot_date` prints `June 8, 2026` (owner
answer A) and is pinned with literals. Round 1 (tree 0c19004): scope-auditor and platform-reviewer PASS. After the PASS
verdicts only wording changed: the unused `date` import in `tests/frontend/test_overflow_menu.py`, and the contract's
`done_when` pattern (`ss-card-footer([^-]|$)`) and one more known limit.

Coordinator evidence:
- `pytest tests` 1515 passed, 1 skipped; `check_context_budget.py` passes.
- Mutations, file restored after each: removing `net_margin_pct` from `DECK_COLUMNS` fails 1 test; restoring the `%d`
  format fails 4; declaring an unused `--ss-*` property fails 1; adding a rule for an unused class fails 1.
- The `done_when` search over `frontend`, `tests`, `docs` for the deleted names finds nothing.
- No browser run: the deck needs Supabase.

follow_ups: `docs/operations_guide.md:250` states the deck fetch as 1.46 MB, measured before the extra column (about 8
bytes a row); re-measure. The class scan counts a class name that only appears in a comment or docstring of another
frontend module, and the custom-property scan reads `styles.py` only; tighten if either bites. `frontend/styles.py`
carries decision and history prose in comments (for example "has shipped six times in this file across three MRs");
clean up in a separate change.

## scope-auditor

VERDICT: PASS
reviewed_tree: 0c19004da4e3c815e0e75c4caa7dabecd9f1348a
risks_checked:
- All nine changed paths are inside `scope_paths`; no preset cutoff, label or card face changed, and the owner answers on defects 17 and 21 are what the diff implements.
- No other `styles.py` rule changed; no documented UI is removed by the deletions; the wireframe in `docs/ui/saved_list.md` already shows the unpadded day.
wording_fixes: applied (unused import, `done_when` pattern).

## platform-reviewer

VERDICT: PASS
reviewed_tree: 0c19004da4e3c815e0e75c4caa7dabecd9f1348a
risks_checked:
- The class and custom-property scans cannot pass on an empty match (floors of 50 and 10), strip CSS comments, and use name boundaries so `ss-card-footer` is not satisfied by `ss-card-footer-shell`.
- `net_margin_pct` exists in `mart_stock_cards`, migration 008 and the `current_cards` view; a session holding old deck rows is refetched once by `deck_rows_lack_columns`.
- `format_snapshot_date` uses no platform-specific directive and keeps its date, ISO, ISO-with-time, bad-string, None and int branches.
wording_fixes: none.
