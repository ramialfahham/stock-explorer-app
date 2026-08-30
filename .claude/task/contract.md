# Task contract

objective: Scope the landing-page/onboarding rework as its own backlog item, per the owner's
  instruction. The owner's original complaint bundled two problems: the one-card-mechanism/
  filters-with-no-visible-effect problem (fixed, `feat/discover-filter-list-focus`, MR !58) and
  the landing page/onboarding experience itself (not fixed, not decided). This task lays out
  the current state and the open product questions, matching the shape used for the earlier
  name-vs-yfinance audit-guard scoping task. It does not choose a design direction: that is a
  §6-reserved product/UX decision, not something this task decides on the owner's behalf.

scope_paths:
  - docs/backlog/landing_onboarding_rework.md
  - .claude/active_work.md
  - .claude/task/contract.md
  - .claude/task/review.md

decisions_reserved:
  - Everything in `docs/backlog/landing_onboarding_rework.md`'s "Open questions" section: what
    "landing" and "onboarding" each mean here, blocking gate vs. progressive disclosure,
    first-time Discover scope, what "getting to the cards where learning content is located"
    should concretely become, the replay path, and whether any candidate direction introduces a
    new mechanism. None of these are answered by this task; they are the owner's call before a
    build contract can be written.
  - Which, if any, of the three candidate directions sketched in the doc is worth pursuing, or
    whether none of them are and a different shape is needed. Presented as discussion starters,
    not a recommendation ranked or defaulted to.

done_when:
  - `docs/backlog/landing_onboarding_rework.md` exists, documents the current landing/onboarding
    implementation as it actually reads in the code (not assumed), quotes the owner's original
    complaint, and lists open questions and candidate directions without resolving any of them.
  - `.claude/active_work.md`'s existing forward-reference to this follow-up (left by the
    Discover filter-list-focus task) is corrected to point at the new doc instead of describing
    it as bare, unlinked prose.
  - No code, test, CI, or dependency file touched: documentation and scoping only.
  - No em dash or en dash on any added line.

impact_map:
  - Documentation only. No frontend, dbt, ingestion, or CI behavior changes.
  - Sets up (but does not start) a future task that will need a task contract of its own once
    the owner answers the open questions above.

amendments: (none)
