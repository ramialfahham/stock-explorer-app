# Task contract
> DISPOSABLE. **Owns:** THIS task's objective, `scope_paths`, reserved decisions and
> `done_when`.
> **Never:** anything that outlives the task. Overwritten by the next task.

objective: A metric's min/median/max range bar never states its own population -- "sector"
  only appears once, higher up the card (e.g. "Industrials (74 companies)"), or in the
  fallback "No sector comparison for this metric." line when there is no mark at all. A
  reader scrolling straight to a metric has no cue the bar is a sector comparison. Owner
  decided (in chat): name it in the metric's own gloss line -- "..., vs sector." -- rather
  than a new word-labels row (already tight on space per docs/ui/card_metric_cell.md's own
  collision notes).

scope_paths:
  - frontend/card_copy.py
  - frontend/card_ui.py
  - tests/frontend/test_card_copy.py
  - tests/frontend/test_card_ui.py
  - docs/ui/card_metric_cell.md
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/active_work.md

decisions_reserved:
  - Wording and placement ("vs sector" folded into the gloss line, not a new row): owner's
    call, in chat.

done_when:
  - `metric_gloss()` takes `benchmarked: bool = False`; when True, inserts ", vs sector"
    before the direction cue (or bare, for the no-direction case).
  - The caller (`_metric_cell_html` in card_ui.py) passes `benchmarked=True` only when
    `_metric_range_html()` actually rendered a mark for that metric on that card -- not
    merely because the metric is catalogue-benchmarkable in the abstract (peer count is
    per-card).
  - The two value-aware early-return branches (net_debt_to_ebitda's "Net cash", debt_to_
    equity's "Negative equity") are untouched -- "vs sector" only applies past them, same as
    the existing universal direction cue.
  - Mutation-proof: a test with the SAME metric on two cards differing only in
    `sector_peer_count` (above/below the peer threshold) asserts "vs sector" appears on one
    and not the other.
  - `pytest tests/ -q` green.

impact_map: Presentation-only in the Streamlit frontend -- no data contract, pipeline, or
  Supabase schema change. No new dependency, no cost.
