# Task contract
> DISPOSABLE. **Owns:** THIS task's objective, `scope_paths`, reserved decisions and
> `done_when`.
> **Never:** anything that outlives the task. Overwritten by the next task.

objective: Refs #47 (MR 1 of 2) -- frontend spec drift and dead code: the docs and the code agree
  on every user-visible claim the audit flagged, and `frontend/` holds no dead definition. No
  behaviour change. Findings 21-29, 31 and 32 of #47. MR 2 takes findings 20 and 30 (behaviour);
  finding 33 stays as documented, no edit.

scope_paths:
  - docs/north_star.md
  - docs/ui/discover_header.md
  - docs/ui/discover_list.md
  - docs/ui/design_system.md
  - docs/ui/card_metric_cell.md
  - docs/data_contract.md
  - docs/metric_layer.md
  - frontend/app.py
  - frontend/card_copy.py
  - frontend/card_ui.py
  - frontend/explore_filters.py
  - tests/frontend/test_benchmark_indicators.py
  - tests/frontend/test_card_copy.py
  - tests/frontend/test_explore_filters.py
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/dead_code_sweep.py

decisions_reserved: all delegated to the agent by the owner in-thread ("act as the expert"),
  each stated with its reason before "go". Finding 21: the code is right (north_star.md is
  reworded to the shipped behaviour). Finding 22: the code is right. Findings 23, 24, 25: the
  code is right. Finding 31: stays UI configuration, one line in metric_layer.md. Finding 32:
  the frontend gate stays and is pinned to dbt's `peer_threshold` by a test. Dead-code boundary:
  a definition is dead when production code never references it; a test counts only when it
  tests live behaviour. A never-passed parameter is removed when it belongs to a retired
  concept or an unreachable branch, and kept (keep list below) when it is an adjustable default
  of live behaviour. Round-1 widening under the working agreement's grep-the-claim rule, from
  reviewer findings: `docs/ui/card_metric_cell.md` and `docs/data_contract.md` each restate a claim
  this MR changes (what the UI shows when a metric has no sector comparison; when the range
  mark is absent).

done_when:
  - `python .claude/task/dead_code_sweep.py` prints `clean` (imports, top-level names, defaulted
    parameters in `frontend/*.py`), with the keep list below as its only exemptions.
  - `git grep -nw -e scope_summary -e walk_meta_line -e walk_progress_line -e VISIBLE_METRICS -e DEEP_DIVE_METRICS -e _METRIC_BASIS_COLUMN -e scope_meta -e show_learn_panel -- frontend tests docs scripts`
    prints nothing, and `git grep -n "tier=" -- frontend tests` prints nothing.
  - `git grep -n "through five" -- docs` and `git grep -n "What do these metrics mean" -- docs frontend tests`
    print nothing; `git grep -n "What each metric means" -- docs frontend` prints exactly the
    `docs/north_star.md` line and the `frontend/card_ui.py` heading.
  - `git grep -n -e "orphan" -e "do not show" -- docs/north_star.md` prints nothing.
  - `git grep -n "924 companies" -- docs/ui` prints one line, without "saved".
  - `docs/ui/design_system.md` no longer says the Yahoo Finance link matches "Save".
  - A test fails if `frontend/card_copy.py`'s `PEER_THRESHOLD` differs from the
    `peer_threshold` set in `dbt_analytics/models/4_intermediate/int_stock__sector_benchmarks.sql`;
    the learn-panel line is built from `PEER_THRESHOLD`.
  - `pytest tests` passes; `python scripts/bootstrap.py --verify` passes.

keep_list:
  - Names read by tests as the catalogue reference: `ALL_METRICS`, `_BY_ID` (`frontend/card_copy.py`).
  - Adjustable defaults of live behaviour: `business_summary_is_truncated.max_words`,
    `business_summary_preview.max_words`, `headline_item_html.max_words`,
    `disclosure_html.wrap_class`, `disclosure_html.details_class`, `normalize_nav_page.fallback`.

known_limits:
  - The sweep counts any identifier token in a non-test file, so a mention in a comment, docstring
    or string, or a name reused in an unrelated module, hides dead code that shares the name. It
    checks a parameter's call sites only when the function has a non-test caller. It lives in the
    disposable `.claude/task/` and nothing runs it; delete it after merge.
  - A card whose `sector_peer_count` is null gets no learn-panel compare section
    (`benchmark_compare_unavailable_learn` returns None); the north_star.md sentence describes
    cards with a peer count.
  - `importance_tier` stays in the metric catalogue seed and `frontend/metrics.json`; after this
    change no frontend code reads it. Removing a seed column is the owner's, so it is a follow-up.

regression_checklist:
  - `pytest tests/frontend` passes with only the tier-split and walk-progress tests removed.
  - The rendered card HTML is unchanged: `build_card_html(card)` equals the old
    `build_card_html(card, scope_meta=None)` output, and `render_stock_card` still renders the
    learn panel then the footer.
  - Every rewritten doc sentence matches the code it describes (placeholder fires for fewer than
    8 peers, a metric with no spread, a per-metric null, a metric not marked benchmarkable).
  - The em-dash, narrative-date, doc-index and doc-path checks pass.
