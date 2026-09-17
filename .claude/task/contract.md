# Task contract
> DISPOSABLE. **Owns:** THIS task's objective, `scope_paths`, reserved decisions and
> `done_when`.
> **Never:** anything that outlives the task. Overwritten by the next task.

objective: Closes #13. Discover's Filters popover gains optional metric range filters. A
  prior attempt (`41217957`, reverted `9a47e07c`) shipped 5 metrics x 2 number_input widgets
  stacked in the popover; reverted for three reasons, all confirmed from the diff: too tall
  on mobile, ambiguous "no filter" state (min/max always showed real numeric bounds, never
  a clearly-empty state), and a Clear button that wrote to already-instantiated widgets'
  session_state -- a hard `StreamlitAPIException`, not a UX papercut.

  Two decisions made via AskUserQuestion before implementation:
  1. **Pattern**: plain-language preset chips (`st.pills`, multi-select), not numeric
     min/max inputs -- sidesteps all three prior failures by construction: chips are
     compact (fits comfortably in the popover), resting/unselected state IS the "no
     filter" state (no sentinel numbers to misread), and there is no separate Clear
     button to mis-order against widget mounting (tap a pill again to deselect).
  2. **The 5 presets and thresholds** (plain, round numbers, not statistically derived
     from production data -- a defensible starting point):
     - High margin: `ebit_margin_pct > 20` (operating) or `net_margin_pct > 20` (financial)
     - Low debt: `net_debt_to_ebitda < 2.0` (operating)
     - Growing revenue: `revenue_growth_yoy_pct > 0` (operating + financial)
     - Strong returns: `statement_roe_pct > 15` (operating + financial)
     - Cash-safe: `cash_runway_months > 18` (pre_revenue)

  A preset whose underlying metric(s) don't exist for a card's `company_type` passes that
  card through untouched -- never excluded for lacking a metric its type doesn't carry,
  the same "omit, never fake" rule the health verdict and metric stack already follow.

scope_paths:
  - frontend/explore_filters.py
  - frontend/app.py
  - tests/frontend/test_explore_filters.py
  - docs/ui/discover_header.md
  - docs/context_budget.yml
  - .claude/task/contract.md
  - .claude/task/review.md

decisions_reserved: none further -- both open questions (pattern, preset list/thresholds)
  were answered via AskUserQuestion this session before implementation.

done_when:
  - `frontend/explore_filters.py`: `METRIC_PRESETS` registry, `card_matches_metric_presets()`
    (pass-through when a card's type lacks the metric), `filter_pool()` and
    `filter_scope_summary()` both accept `metric_presets`.
  - `frontend/app.py`: `st.pills` (multi-select, unkeyed, same eviction-safe pattern as the
    market/sector selectboxes) renders below Sector in the Filters popover;
    `_discover_pool()` passes active presets through to `filter_pool()`.
  - No dedicated Clear control -- verified live that tapping an active pill deselects it
    cleanly, no `StreamlitAPIException`, no leftover state (matches the specific crash
    mode the prior attempt hit).
  - Verified live against a running dev server (not just tests): single preset filters
    correctly, two presets combine with AND semantics, deselecting restores the full pool,
    the closed-Filters summary line lists active preset labels in a stable order.
  - `docs/ui/discover_header.md` documents the pills in the Filters popover section and the
    vertical-order table. `docs/context_budget.yml`'s budget for that file raised 8000 ->
    9000 after one trim pass, per the checker's own sanctioned remedy (two legitimate
    features -- persistent search, now preset filters -- both needed real doc space in
    close succession).
  - `pytest tests/frontend/ -q` green, with new coverage: preset options/labels, pass-through
    for a card whose type lacks the metric, each preset's threshold direction, multiple
    presets requiring all to pass, `filter_pool` with/without presets, `filter_scope_summary`
    with/without active presets.

impact_map: frontend-only. One new registry + two new functions in `explore_filters.py`;
  `filter_pool`/`filter_scope_summary` gain an optional keyword-only parameter (backward
  compatible, existing call sites unaffected without it). One new widget block in
  `app.py`'s `_render_explore_filters`. No schema, dbt, ingestion, or CI change.
