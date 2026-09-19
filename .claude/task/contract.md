# Task contract
> DISPOSABLE. **Owns:** THIS task's objective, `scope_paths`, reserved decisions and
> `done_when`.
> **Never:** anything that outlives the task. Overwritten by the next task.

objective: Owner-reported bug: "removing the filters seemed to be buggy, not going back to
  the full sample of companies." Root cause, found by live reproduction across single- and
  multi-filter scenarios, was not in filter removal itself -- the market/sector/metric-preset
  widget state machinery is unkeyed by design (documented eviction-avoidance pattern) and
  verified working correctly throughout. The real bug: two of five metric-preset filters
  ("Low debt": `net_debt_to_ebitda`, "Growing revenue": `revenue_growth_yoy_pct`) checked
  fields absent from `DECK_COLUMNS`, the slim column set the Discover/Saved list fetches.
  `_card_matches_preset`'s "omit, never fake" rule treats a missing metric value as an
  automatic pass, so both presets silently matched every card regardless of real debt/growth
  -- selecting either did nothing, and removing one while another (also broken) preset stayed
  selected looked like "removal doesn't restore the full sample."

  Fix: added both fields to `DECK_COLUMNS`. Verified against live production Supabase data
  (paginated, deduped to latest snapshot -- matching what the app itself does): "Low debt"
  alone narrows 1023 -> 617; "Low debt" + "Growing revenue" together -> 546; removing just
  "Low debt" -> 878 (the correct "Growing revenue"-only count, not a reset to 1023 and not
  stuck at 546). This is the exact reported scenario, confirmed fixed live in the browser.

  Separately investigated whether "Cash-safe" (pre_revenue only) should be hidden when its
  target population is empty -- first diagnosed as always-empty (0 pre_revenue cards) from
  an unpaginated, undeduped scratchpad query; owner asked to hide it on that basis. Redone
  properly (full pagination + dedup): 2 eligible pre_revenue cards actually exist
  (au_asx200/DYL, au_asx200/NXG), so the population is not empty -- corrected this to the
  owner before proceeding. Built `metric_preset_options()` as a general, data-driven guard
  (hides a preset only when its target company type(s) have zero eligible cards in the
  current deck) rather than a hardcoded hide, so it doesn't act on the disproven premise.
  Live-tested selecting "Cash-safe" alone: count stays at 1023 (both pre_revenue cards pass
  the check -- one genuinely, one via the same omit-on-missing-data rule), so it's still
  visually inert today, for a different reason (nothing in a real, non-empty population
  currently fails it) than the one first reported. Owner decision on record: leave it
  visible as-is; no further code change for that case.

scope_paths:
  - frontend/supabase_cards.py
  - frontend/explore_filters.py
  - frontend/app.py
  - tests/frontend/test_explore_filters.py
  - .claude/task/contract.md
  - .claude/task/review.md

decisions_reserved: Cash-safe hide-when-empty vs leave-visible was escalated after the
  premise correction -- owner chose "leave visible as-is" (§6 metric-preset visibility is a
  product call). No other decision reserved: the DECK_COLUMNS fix was owner-requested
  directly ("what is it that you suggest" -> this fix, confirmed after deeper verification).

done_when:
  - `DECK_COLUMNS` includes `net_debt_to_ebitda` and `revenue_growth_yoy_pct`, with the
    justifying comment block updated per this list's own "minimal and justified" convention.
  - `metric_preset_options(cards)` excludes a preset only when every company type its checks
    target has zero eligible cards in `cards`; an omitted/empty `cards` still returns all
    five (unchanged default for any caller with no deck in scope).
  - `frontend/app.py`'s one call site passes the current deck's `cards` in.
  - `pytest tests/frontend/test_explore_filters.py` covers: the no-cards fallback, hiding a
    preset with zero eligible cards of its type, keeping a preset visible when its type is
    present, and ignoring ineligible cards when computing type presence.
  - `pytest tests/` (full suite, 844 tests) passes.
  - `check_no_em_dash.py` passes on the changed files.
  - Live-verified against the real Streamlit dev server + production Supabase data (not
    simulated): the exact reported multi-filter-removal scenario, both newly-functional
    presets individually, and Cash-safe's current (correct, data-driven) visibility -- done,
    documented above.

impact_map: frontend/supabase_cards.py (DECK_COLUMNS, two more float columns on the cold
  list-view fetch path, ~50-60 KB measured against an existing view of Supabase row sizes),
  frontend/explore_filters.py (metric_preset_options signature + behavior change),
  frontend/app.py (one call site updated to match), matching test coverage. No schema/CI
  change. `_ensure_all_cards`'s existing `deck_rows_lack_columns` self-heal already handles
  the stale-cache-shape transition for any session with a warm cache from before this merge.
