# Task contract

objective: Record the owner's decision on Discover's first-time default scope, reached in
  conversation (not a mockup or exploration cycle): no change. The premise behind scoping this
  as a problem conflated two different kinds of "beginner" (new to reading financial fundamentals
  versus new to using a web app); this app's audience is the former, and a filterable, searchable
  list isn't intimidating to that audience. The full unfiltered list stays on first load, for
  every visitor, every time. This closes `docs/backlog/discover_first_time_default.md` with a
  decision rather than leaving it open, and corrects `docs/backlog/landing_onboarding_rework.md`'s
  cross-reference to match.

scope_paths:
  - docs/backlog/discover_first_time_default.md
  - docs/backlog/landing_onboarding_rework.md
  - .claude/active_work.md
  - .claude/task/contract.md
  - .claude/task/review.md

decisions_reserved: (none; this task records a decision the owner already made, it does not make
  one)
  - **Found by round-1 scope-auditor review: an earlier draft violated the line above.** Marking
    the "does this conflict with, or complement, the still-separately-open 'getting to the
    cards' question" open question as moot went further than mootness and asserted the two
    questions were "unrelated," a substantive judgment the owner's actual reasoning never made
    and this task was never asked to make. It also directly contradicted unchanged prose earlier
    in the same file describing the two as "may or may not be related." Fixed: reworded to state
    only that this decision made no change to compare the two questions against, without
    characterizing whether they relate.

done_when:
  - `docs/backlog/discover_first_time_default.md`'s Status line and a new "Decision" section
    record the resolution and the reasoning (the beginner-conflation premise was wrong), all
    four candidate directions are marked with which one was chosen and why the others weren't,
    and every previously-open question is marked resolved or moot, not left reading as open.
  - `docs/backlog/landing_onboarding_rework.md`'s "First-time Discover scope" bullet moves from
    "Still open, not touched by this decision" to a "Resolved separately" note pointing at the
    dated outcome, since it's no longer accurate to describe it as still open.
  - `.claude/active_work.md` records the decision and its reasoning where a fresh session would
    see it, flagged so the same beginner-conflation mistake isn't repeated on a future "simplify
    the first visit" idea.
  - No code, test, CI, or dependency file touched: documentation only, since the decision is "no
    change."
  - No em dash or en dash on any added line.

impact_map:
  - Documentation only. No frontend, dbt, ingestion, or CI behavior changes; nothing in the app
    itself changes as a result of this decision.

amendments: (none)
