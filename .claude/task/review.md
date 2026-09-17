# Review
> DISPOSABLE. **Owns:** verdicts + diff hash for THIS task's staged change.
> **Never:** narrative of how the round went. Overwritten by the next task.

diff_sha256: b9e06bf1c3b44f542d928c725e3330cd13c9bceb5c574556d200bd9d1a05be87

## scope-auditor
VERDICT: PASS
risks_checked:
- All 7 changed files in `scope_paths`; every `done_when` item verified against the diff.
- Backward compatibility: `filter_pool()`/`filter_scope_summary()` gain an optional
  `metric_presets` keyword parameter with empty default; existing call sites unaffected.
- Pass-through correctness: a card whose type has no matching preset check, or is missing
  that check's specific metric value, is never excluded -- verified against the diff and
  its dedicated tests.
- Both owner-level decisions (preset pattern, preset list/thresholds) were pre-approved
  via AskUserQuestion; no silent decisions in the diff.

## cto-reviewer
VERDICT: PASS
risks_checked:
- **Round 1 FAILED**: `high_margin`'s two checks (`ebit_margin_pct` for operating,
  `net_margin_pct` for financial) were selected by "is this metric non-null," not by the
  card's actual `company_type`. `int_stock__card_metrics.sql` computes both metrics
  independently of `company_type` (no gate), so most operating cards also carry a non-null
  `net_margin_pct` -- the old code silently required BOTH margins to clear 20%, over-
  excluding operating cards with a strong operating margin but a thinner net margin.
- **Round 2: fixed and verified.** `METRIC_PRESETS` now scopes every check by
  `(company_type, metric, op, threshold)`; `_card_matches_preset` filters by
  `card["company_type"] == ctype`, not metric presence. Confirmed by direct code read and
  the new regression test `test_card_matches_metric_presets_operating_ignores_a_co_populated_net_margin`
  (operating card with both `ebit_margin_pct=25.0` and `net_margin_pct=2.0` set still
  matches `high_margin`). Checked for a new bug from reusing the same metric name across
  two `company_type` scopes (`growing_revenue`, `strong_returns`) -- not exploitable, since
  a card has exactly one `company_type`, so at most one same-named tuple can ever apply.
- `st.pills` widget genuinely safe from the eviction/identity-churn issues this file has
  hit before: `explore_metric_presets` is never written from the pill's own output before
  being read on the same run, unlike the `_search_query_widget` case from a separate task.
- `docs/context_budget.yml`'s raise (8000->9000 for `discover_header.md`) is justified by
  the diff's genuine new content, not an unexplained widening.
- Preset-filter-before-dedup ordering in `filter_pool`: investigated, found consistent with
  the PRE-EXISTING market/sector filter ordering (which already runs before dedup) -- left
  as-is by design, not a regression this diff introduces.
- `pytest tests/frontend/test_explore_filters.py -q` run directly both rounds: 46 passed.

## Verified independently

- `pytest tests/frontend/ -q` -- 313 passed (full frontend suite, both rounds).
- `python scripts/check_no_em_dash.py`, `check_context_budget.py` -- passed.
- Live-verified against a running dev server (`streamlit run streamlit_app.py`) with real
  production-shaped data, both before and after the round-1 fix: single preset (High
  margin: 1021 -> 476 companies), two presets combined (AND semantics, summary line lists
  both labels), deselect (clean revert to unfiltered pool, no crash -- confirms the specific
  failure mode, `StreamlitAPIException` on Clear, that sank the prior attempt, does not
  recur with this pattern).
