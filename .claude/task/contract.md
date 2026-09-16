# Task contract
> DISPOSABLE. **Owns:** THIS task's objective, `scope_paths`, reserved decisions and
> `done_when`.
> **Never:** anything that outlives the task. Overwritten by the next task.

objective: Closes #7. Dual-index companies (e.g. Airbus, a constituent of both the DAX and
  CAC 40, both resolving to the same yfinance symbol `AIR.PA`) currently appear as two
  separate cards in Discover's "All markets" view, differing only by `market_code`. The
  underlying data is correct -- the company genuinely belongs to both indices -- so the fix
  is display-layer dedup, not a data change. `frontend/explore_filters.py` already dedupes
  by `(market_code, ticker)` across snapshot dates (`dedupe_to_latest_snapshot`, applied
  upstream in `supabase_cards.py`); this task adds the analogous ticker-only dedup, scoped
  to `filter_pool()` and only when `market_code == ALL_MARKETS` -- a market-scoped view
  (e.g. "DAX only") must still show the company once per market it's actually filtered to.

scope_paths:
  - frontend/explore_filters.py
  - tests/frontend/test_explore_filters.py
  - .claude/task/contract.md
  - .claude/task/review.md

decisions_reserved: none. The issue's own text already names the fix location and pattern
  (extend the existing `dedupe_to_latest_snapshot` approach); no product/UX ambiguity --
  issue #7 explicitly defers "which market should own a dual-listed company" as out of
  scope, since dedup picks a winner arbitrarily (latest snapshot) and both rows carry
  identical card content besides `market_code`/`sector` display.

done_when:
  - `filter_pool(cards, interactions, market_code=ALL_MARKETS, sector=...)` returns at most
    one row per ticker, even when two input cards share a ticker but differ in
    `market_code`.
  - `filter_pool(..., market_code="de_dax", ...)` (a single-market scope) is unaffected --
    still returns every eligible row for that market; the dedup only fires for
    `ALL_MARKETS`.
  - New test covers the dual-index collapse case and confirms a single-market filter is
    untouched.
  - `pytest tests/frontend/test_explore_filters.py -q` green.
  - `sqlfluff` not applicable (no SQL touched). `check_context_budget.py`,
    `check_no_em_dash.py` pass on the staged diff.

impact_map: frontend-only change, one function in `explore_filters.py` plus its call site
  inside `filter_pool`. No schema, dbt, ingestion, or CI change. No product/UX decision --
  pure display-layer bug fix per the issue's own scoped recommendation.
