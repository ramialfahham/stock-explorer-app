# Task contract

objective: Scope Discover's first-time default scope as its own backlog item, per the owner's
  request. This question was flagged in `docs/backlog/landing_onboarding_rework.md`'s "Still
  open" list as deliberately not answered by `feat/kill-landing-screen`'s decision to delete the
  landing screen. This task lays out the current mechanism and the open product questions,
  matching the shape used for the two earlier scoping tasks this session (the name-vs-yfinance
  audit guard, and the landing/onboarding rework itself). It does not choose a direction: that is
  a §6-reserved product decision (it touches a locked `north_star.md` rule), not something this
  task decides on the owner's behalf.

scope_paths:
  - docs/backlog/discover_first_time_default.md
  - docs/backlog/landing_onboarding_rework.md
  - .claude/active_work.md
  - .claude/task/contract.md
  - .claude/task/review.md

decisions_reserved:
  - Everything in `docs/backlog/discover_first_time_default.md`'s "Open questions" section:
    whether "first-time" is worth building for at all versus changing the default for every
    session, what would count as "first-time" if it is, what the smaller starting point would
    actually be, whether this relates to the still-separately-open "getting to the cards"
    question, and whether any option beyond changing `default_market_filter()`'s return value
    for everyone counts as a new mechanism needing sign-off. None of these are answered by this
    task; they are the owner's call before a build contract can be written.
  - Which, if any, of the four candidate directions sketched in the doc is worth pursuing, or
    whether none of them are. Presented as discussion starters, not a recommendation ranked or
    defaulted to.

done_when:
  - `docs/backlog/discover_first_time_default.md` exists, documents the current default-scope
    mechanism as it actually reads in the code (not assumed), including the specific, verified
    fact that `feat/kill-landing-screen` deleted the only piece of state that ever distinguished
    a returning visitor from a first-time one (`onboarding_dismissed`), even though that flag was
    never wired to the Discover default itself. Lists open questions and candidate directions
    without resolving any of them.
  - `docs/backlog/landing_onboarding_rework.md`'s "First-time Discover scope" bullet is corrected
    to point at the new doc instead of describing it as unlinked prose.
  - `.claude/active_work.md`'s handover reflects the new scoping doc and its key finding (the
    now-missing first-time signal), and separately corrects a leftover status header from the
    prior task (`feat/kill-landing-screen`'s entry still said "MR !61 OPEN" after the MR had
    already been merged and cleaned up).
  - No code, test, CI, or dependency file touched: documentation and scoping only.
  - No em dash or en dash on any added line.

impact_map:
  - Documentation only. No frontend, dbt, ingestion, or CI behavior changes.
  - Sets up (but does not start) a future task that will need a task contract of its own once
    the owner answers the open questions above.

amendments: (none)
