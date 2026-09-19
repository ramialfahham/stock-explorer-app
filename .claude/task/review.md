# Review
> DISPOSABLE. **Owns:** verdicts + diff hash for THIS task's staged change.
> **Never:** narrative of how the round went. Overwritten by the next task.

diff_sha256: ac1f1dbd417acabf2c08a636338859adaee6810799064ed0774c647863c460f3

## cto-reviewer
VERDICT: PASS
risks_checked:
- Cost (query bytes): `DECK_COLUMNS` in `frontend/supabase_cards.py` gains
  `net_debt_to_ebitda` and `revenue_growth_yoy_pct`, adding to every visitor's cold-path
  fetch. Contract quantifies this at ~50-60 KB against an existing ~1.4 MB payload and
  states the owner participated in choosing this fix over alternatives (hiding/removing the
  broken presets). No unilateral cost decision -- held.
- Re-run / cache-staleness safety: a session holding a warm `all_cards` cache from before
  this merge would hold rows missing the two new columns. Verified in `frontend/app.py`
  lines 152-159 that `_ensure_all_cards` already calls
  `deck_rows_lack_columns(cards, DECK_COLUMNS)`, and on a shape mismatch clears both
  `_cached_deck` and `session_state["all_cards"]` before refetching -- no code change needed
  for this transition, confirmed by reading the existing self-heal path rather than trusting
  the contract's claim. Held.
- New mechanism / scope: `metric_preset_options()` gains a `cards` parameter on an existing
  pure function -- not a new dependency, service, or lifecycle hook. Its one call site
  (`frontend/app.py:482`) was updated to match. Every file in the diff is listed in
  `scope_paths`; no CI, hook, or plugin config touched. Held.

## scope-auditor
VERDICT: PASS
risks_checked:
- Function signature change from `metric_preset_options()` to
  `metric_preset_options(cards: Iterable[dict[str, Any]] = ())` maintains backward
  compatibility via default parameter; the only call site in app.py is updated to pass
  `cards`. Default behavior (empty list returns all presets) preserved for callers with no
  deck context.
- Bug-fix mechanism: missing `net_debt_to_ebitda` and `revenue_growth_yoy_pct` columns are
  added to `DECK_COLUMNS`, ending the omit-never-fake rule's false passes. The new
  `metric_preset_options()` defensively filters cards by `is_card_eligible` and handles
  missing `company_type` via `.get()`, correctly excluding ineligible cards when computing
  which preset types are actually present in the deck.
