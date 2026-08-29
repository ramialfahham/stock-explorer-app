# Task contract

objective: Scope the name-vs-yfinance audit-guard mechanism as its own backlog item, so the
  open design questions and acceptance criteria are recorded in one place instead of scattered
  across three task contracts (Nikkei, SMI, Block ticker) that each flagged it and moved on.
  Scoping only: no code, no CI change. Owner asked to "scope it as its own task" 2026-08-29.

scope_paths:
  - docs/backlog/name_vs_yfinance_audit_guard.md
  - docs/north_star.md
  - .claude/active_work.md
  - .claude/task/contract.md
  - .claude/task/review.md

decisions_reserved:
  - This is a scoping document, not an implementation. Every open question inside it
    (live-fetch vs cached snapshot, fuzzy-match tolerance, CI cadence, hard-fail vs
    warning-only) is explicitly left for the owner to answer when this item is picked up, not
    answered here.
  - No new dependency, script, or CI step is added by this task. Writing the backlog doc is not
    the same decision as building the mechanism it describes.

done_when:
  - `docs/backlog/name_vs_yfinance_audit_guard.md` exists, matching the shape of the one
    existing backlog doc (`docs/backlog/discover_metric_filters_phase2.md`): Status, Summary,
    Context, open questions, draft acceptance criteria, Related.
  - Context section is accurate against what actually happened this session, not a generic
    restatement: cites the specific gap (2 of 11 Nikkei defects caught by the existing
    collision-based guard, 9 missed) with the real numbers, not rounded or invented ones.
  - `docs/north_star.md`'s "Phase 2 backlog" table is NOT used for this item: that table is
    product-engagement backlog (stickiness + depth), and this is a data-quality/CI mechanism,
    a different category. Confirmed by reading the table's own heading and its one existing
    row before deciding not to add to it, rather than assumed.
  - `.claude/active_work.md`'s existing mention of this idea (the "durable fix is checking each
    seed name against yfinance's `info_long_name`" paragraph, written during the Nikkei task) is
    updated to link to the new backlog doc instead of leaving the idea as bare prose with no
    pointer.
  - No em dash or en dash on any added line.

impact_map: (none: documentation only, no code or data path touched)

amendments: (none)
