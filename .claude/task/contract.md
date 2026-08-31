# Task contract

objective: Remove the Discover list's verdict dot entirely, per explicit owner instruction
  ("Dots misaligned, just remove them") given after MR !65's CSS-drawn-circle fix apparently
  still did not resolve the owner's perception of misalignment. This is a full removal, not
  further alignment debugging: `build_rich_row_html` drops its `verdict` parameter, the list
  row renders title/subtitle/metric only, and every doc describing the list row is updated to
  match. The Company Snapshot card's own separate verdict badge (`card_ui.py`'s
  `.ss-verdict-badge`/`.ss-verdict-emoji`/`.ss-verdict-label`) is untouched -- the owner's
  complaint and screenshot were specifically about the list, not the card.

scope_paths:
  - frontend/row_ui.py
  - frontend/app.py
  - frontend/styles.py
  - frontend/card_copy.py
  - tests/frontend/test_row_ui.py
  - tests/frontend/test_card_copy.py
  - docs/ui/discover_list.md
  - docs/ui/design_system.md
  - docs/ui/saved_list.md
  - docs/ui/discover_header.md
  - docs/backlog/discover_list_performance.md
  - docs/north_star.md
  - README.md
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/active_work.md

decisions_reserved: none for this task -- the removal itself is a direct, unambiguous owner
  instruction, not a call being made on the owner's behalf. Two adjacent questions raised in
  the same owner message are explicitly OUT of this task's scope and are not being decided or
  implemented here:
  - Whether the list row should show any lead metric at all (owner said "I'm not sure," an
    open question to discuss in chat, not to implement).
  - Third-party (Gemini) feedback on verdict methodology and metric-range scaling, to be
    verified against the codebase and filed as a backlog doc for later discussion, not acted
    on now.

done_when:
  - `build_rich_row_html` takes `(title, subtitle, metric)`, no verdict parameter, and renders
    no verdict markup at all.
  - `render_rich_row_list` drops its `verdict_fn` parameter; the Discover call site no longer
    computes or passes a verdict.
  - `frontend/app.py`'s `_discover_row_verdict` helper is deleted (no longer used anywhere).
  - `frontend/styles.py` has no remaining `.ss-row-verdict*` rules or `--ss-verdict-*` tokens
    (confirmed unused before removal, not just deleted blind).
  - `tests/frontend/test_row_ui.py` matches the new 3-argument signature; no test asserts on
    verdict markup for the list row.
  - `docs/ui/discover_list.md`, `docs/ui/design_system.md`, `docs/north_star.md`, `README.md`
    no longer describe a verdict dot/badge on the list row (card-level verdict-badge
    references, which are a different component, are left untouched).
  - Repo-wide grep for `ss-row-verdict`, `--ss-verdict-`, `verdict_fn`, `_discover_row_verdict`
    returns no hits outside the card-level badge (`card_ui.py`'s `.ss-verdict-badge` family).
  - `pytest` green.
  - Live verification: Discover list renders with no dot, the lead metric still renders,
    `.ss-row-side` holds only the metric span, and the row's tap target still resolves
    correctly at both its top and bottom edge (`document.elementFromPoint`), confirming MR
    !67's fix is unaffected by this content change.
  - No em dash or en dash on any added line.

impact_map:
  - Discover list rows only; Saved and Search use the plain row (`build_row_html`), unaffected.
  - The Company Snapshot card's own verdict badge is a separate component and is untouched.
  - CSS/HTML/Python display-layer change only; no data model, dbt, or ingestion change.
  - `docs/north_star.md`'s "List row" rule is a locked product rule being amended here under
    explicit owner authorization (the instruction to remove the dot), per working-agreement §6.

amendments: (none)
