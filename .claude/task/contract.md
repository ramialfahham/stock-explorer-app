# Task contract

objective: Remove the dead `benchmark_indicator()`/`_BENCHMARK_INDICATORS` glyph helper
left behind when Slice 6c replaced arrow glyphs with word-based benchmark labels, without
losing test coverage for the still-live helpers in the same file (`benchmark_position`,
`benchmark_indicator_label`, `benchmark_compare_unavailable_learn`).

scope_paths:
  - frontend/card_copy.py
  - tests/frontend/test_benchmark_indicators.py
  - .claude/active_work.md
  - .claude/task/contract.md

decisions_reserved:
  - (none) — this is item 1 of 3 already-listed "Next concrete actions" in
    active_work.md; the owner picked this one explicitly ("go ahead") over the other two
    (sector data-quality issue, CSS-specificity audit).

done_when:
  - `_BENCHMARK_INDICATORS` and `benchmark_indicator()` no longer exist in
    frontend/card_copy.py.
  - No remaining reference to either symbol anywhere in the repo (grep clean).
  - `benchmark_indicator_label()`, `benchmark_position()`, and
    `benchmark_compare_unavailable_learn()` keep their existing test coverage — no net
    loss, since they are still production code (card_ui.py's `_benchmark_compare_body`
    and `build_learn_panel_body_html`).
  - Full test suite passes (`python -m pytest tests/ -q`).
  - active_work.md's "Next concrete actions" item 1 updated to reflect this is done.

amendments:
  - 2026-08-24 — initial contract, written after implementation (small, mechanical,
    pre-scoped by the owner's own handover entry — see decisions_reserved).
  - 2026-08-24 — added .claude/task/contract.md to its own scope_paths, matching the
    prior task's precedent; scope-auditor round 1 FAILed on its absence.
