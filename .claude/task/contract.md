# Task contract

objective: Record the owner's decision on "getting to the cards where learning content is
  located", the last unresolved part of the owner's original landing/onboarding complaint,
  reached by directly inspecting the real, live focus card rather than theorizing about it: no
  change needed. One tap from the Discover list, a reader already sees a plain-English
  AI-written verdict paragraph and six lensed metrics, each with a plain-language gloss line
  (a sector comparison too, but only for the metrics the catalogue marks benchmarkable, ~4 of
  13; the rest correctly say "No sector comparison for this metric" rather than fake one). One
  further tap reaches, immediately, a median-comparison recap, a short analogy per metric, and
  an interactive playground; each metric's fuller written explanation needs its own additional
  "Read more" tap, by design. The path to real, plain-language content is one to two taps and
  the destination is substantial; the original worry that content was hard to reach doesn't
  hold up against what's actually built. This closes `docs/backlog/landing_onboarding_rework.md`'s
  last open question, so that doc is now fully resolved: all three parts of the owner's original
  complaint (the one-card mechanism, the landing screen, and getting to the cards) are closed.

scope_paths:
  - docs/backlog/landing_onboarding_rework.md
  - .claude/active_work.md
  - .claude/task/contract.md
  - .claude/task/review.md

decisions_reserved: (none; this task records a decision the owner already made, it does not make
  one)
  - **Found by round-1 scope-auditor review: the recorded evidence overclaimed what the live
    app actually showed.** The first draft said all six metrics on the card got a plain-language
    gloss AND a sector comparison, and that one tap into "Understand these numbers" reached
    fuller per-metric explanations, not just analogies. Both were checked against source rather
    than accepted: `dbt_analytics/seeds/metric_catalogue.csv`'s `benchmarkable` column shows only
    4 of 13 metrics ever get a sector comparison, so a six-metric card always has at least two
    reading "No sector comparison for this metric" instead (`frontend/card_ui.py`, documented
    behavior per `docs/ui/card_metric_cell.md`); and `frontend/card_ui.py`'s
    `_metric_learn_block_html` gates each metric's fuller explanation behind its own additional
    "Read more" toggle, one more tap per metric, matching `docs/north_star.md`'s Deep-tier
    description exactly. The interactive playground (`frontend/metric_school.py`) genuinely is
    reachable with the one tap, unconditional, not gated by any "Read more." Fixed: reworded to
    the precise mechanics, which still support the same overall conclusion (no change needed).

done_when:
  - `docs/backlog/landing_onboarding_rework.md`'s "getting to the cards" bullet moves from
    "Still open, not touched by this decision" to "Resolved separately," with the concrete
    evidence from the live app (not assumed from the code) that grounds the resolution.
  - `docs/backlog/landing_onboarding_rework.md`'s Status line reflects that the doc is now fully
    resolved: all three parts of the owner's original complaint are closed, not just some.
  - `.claude/active_work.md` records the decision and its evidence where a fresh session would
    see it.
  - No code, test, CI, or dependency file touched: documentation only, since the decision is "no
    change."
  - No em dash or en dash on any added line.

impact_map:
  - Documentation only. No frontend, dbt, ingestion, or CI behavior changes; nothing in the app
    itself changes as a result of this decision.

amendments: (none)
