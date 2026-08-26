# Task contract

objective: Make the health verdict read revenue growth on the operating and bank cards, so
  that every metric a card shows feeds the verdict. Growth enters as a ONE-SIDED axis: a
  shrinking top line blocks green, growth never earns green, and growth never causes red.
  Step 2 of three; sector-calibrated thresholds are step 3 and are NOT in this branch.

scope_paths:
  - scripts/assessment_rules.py
  - scripts/seed_ci_raw_fixtures.py
  - docs/data_contract.md
  - docs/ui/card_metric_cell.md
  - docs/ux_principles_finanz_lern_apps.md
  - dbt_analytics/**
  - frontend/card_copy.py
  - frontend/card_ui.py
  - frontend/metric_school.py
  - tests/**
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/active_work.md

decisions_reserved:
  - **Growth is one-sided, and that is the whole design.** It can block green; it can never
    cause red and never earns green. Growth was excluded from the verdict originally for a
    good reason — a company can grow into losses, so high growth is not health — and the
    owner's rule ("if we don't use a metric for the verdict then we don't show it") had to
    be satisfied without discarding that reasoning. One-sidedness does both: a shrinking
    business is a genuine health risk, a fast-growing one has proved nothing about
    resilience. Do NOT "simplify" this later into a symmetric good/weak axis.
  - **Threshold is 0%, owner-decided 2026-08-26.** Any year-over-year decline blocks green.
    The agent proposed -5% on the argument that a single quarter is noisy; the owner rejected
    it ("Then you have never talked to a CFO"). That rejection is correct on the mechanics
    too: YoY compares the same quarter a year earlier, so it already controls for
    seasonality, and the "noise" framing was wrong rather than merely cautious. Revenue going
    backwards is a signal, not measurement error. **Do not reintroduce a tolerance band.**
  - **`burn_rate_monthly` stays shown but unread, a deliberate exception to the owner's own
    rule.** Owner-decided in the same exchange, after the agent's first justification was
    challenged and partly withdrawn. What survives: cash runway is a RATIO, and a ratio
    destroys magnitude. Two companies both showing 18 months — one burning $2M/month on $36M,
    one burning $50M/month on $900M — are completely different businesses, and burn is the
    only number on the card that says which one you are looking at. It also shows the lever,
    since runway moves either by raising cash or cutting spend and the quotient hides which.
    **The argument that did NOT survive:** that a reader can check the arithmetic. They
    cannot — runway is cash / burn but the card shows NET cash (cash minus debt), so the sum
    does not reconcile from displayed numbers. Do not repeat that justification.
  - Not a new decision: making the verdict read burn as its own axis would double-count, since
    runway already IS cash divided by burn.
  - **The LLM prompt's growth rule had to change, and that is §6 owner-signed content.** It
    told the model growth is "context only, not a health signal", which the verdict now
    contradicts. Left alone it would have been worse than stale: the cards downgraded by this
    change regenerate their prose, so each new paragraph would be written under an instruction
    denying the reason for its own downgrade. Owner approved the replacement wording in-session.
    The anti-advice guard is preserved in substance, not verbatim: "never treat high growth as
    a reason to buy" became "is never a reason to buy", and the sentence "The verdict measures
    financial health and resilience only" was dropped because the verdict now also reads
    growth. A third thing went with them: a parenthetical telling the model that no P/E or
    price-to-book figure exists. It was a changelog line the owner had already rejected from
    the prompt, and it is redundant anyway since no valuation field is passed. All three
    changes are owner-approved.

  - **OPEN, escalated to the owner, NOT resolved in this branch: the growth metric's card copy
    now argues with the badge.** `metric_catalogue.csv`'s `learn` text for
    `revenue_growth_yoy_pct` reads "One quarter can be noisy, so look for a pattern over time",
    and it RENDERS, in "Understand these numbers" on exactly the two card types this gate
    applies to. On the 32 downgraded cards a reader sees a badge that moved Healthy to Mixed on
    one quarter, and one click away is text telling them one quarter is noisy. The copy was
    consistent while growth was shown-and-unread; this branch is what makes it contradictory.
    A second, related gap: every base-effect caveat in that copy warns about the UPSIDE only
    ("a small prior-year base can inflate the percentage"), while the downside is now the
    actionable half, and nothing warns that an inflated prior-year base can manufacture a
    decline. **To be accurate about why it is untouched: the seed IS inside `scope_paths` via
    `dbt_analytics/**`, so this was a choice, not a scope limit.** It is §6 user-visible metric
    copy and the owner rewrites it, not the agent.

done_when:
  - `_verdict_operating` and `_verdict_financial` read `revenue_growth_yoy_pct`: growth below
    0% blocks green and does nothing else. Red is bit-for-bit unchanged for every card.
  - A null growth value never blocks green — absent data is not a decline.
  - `INPUT_FIELDS_BY_TYPE` is unchanged (growth was already in the hashed input set, so the
    prose read already saw it; only the verdict changes).
  - Tests pin the one-sidedness explicitly: a card with strong growth and weak fundamentals
    does not become green, and a card with excellent fundamentals and a shrinking top line
    does not become red.
  - pytest passes; the layer/doc/sql gates pass.
  - `docs/data_contract.md`'s verdict section states the growth axis and its one-sidedness.
  - Review cycle: scope-auditor, cto-reviewer, equity-analyst-reviewer and
    analytics-engineer-reviewer (`*.sql`, `dbt_analytics/*.yml`) PASS. More than the three this task would suggest, because the date-stamp sweep pulled dbt
    and frontend files into the diff and the routing follows the files, not the intent.
    data-engineer-reviewer is NOT required: no `supabase/*` file is staged (see below).

impact_map: Two behavioural changes. The verdict itself, and the prose on every card: the
  prompt was corrected and `INPUT_HASH_VERSION` bumped, so all ~910 stored reads rewrite. No metric definition, no seed and no
  schema change. The diff does touch dbt models, frontend modules and a dbt test, but only in
  comments and column descriptions, as part of removing the scattered date stamps.
  - **Measured: 32 cards move green -> yellow, nothing else moves.** Measured against the 907
    rows of the 2026-08-24 snapshot, which is NOT the whole deck: the app serves 910, because
    the frontend keeps the newest row per ticker and BXB/RMS/SPK survive from an older
    snapshot. Three live cards are outside the measurement. The baseline also predates merged
    step 1, which widened eligibility, so the absolute before/after totals below will not be
    what the next run shows. Only the isolated delta of this change holds.
    Green 264 -> 232. Yellow 372 -> 404. Red 271 -> 271, unchanged, which is the design working.
  - Every one of those 32 is a company the app currently calls "Healthy" while its revenue is
    shrinking year over year.
  - **This changes an already-shipped, user-visible verdict on 32 live cards** (§6). It is the
    point of the branch, not a side effect, but it is the reason the branch exists at all and
    must be stated plainly in the MR.
  - **Every stored AI read regenerates on the next run: roughly 910 Haiku calls.** The verdict
    alone would have regenerated only the 32 cards whose colour moved, because the hash covers
    the verdict. But the PROMPT changed too, and the hash does not cover the prompt, so the
    other ~875 cards would have kept prose written under an instruction telling the model
    growth is "not a health signal", which is the exact contradiction this branch exists to
    remove. `INPUT_HASH_VERSION` is bumped to `5a.3` to force them all. Owner-approved: API
    volume is a §6 cost decision and the run was already scheduled.
  - `burn_rate_monthly` remains shown and unread on the 3 pre-revenue cards, by owner decision
    recorded above.

amendments:
  - Owner rejected a changelog line the agent had previously put inside `READ_SYSTEM_PROMPT`
    ("And why is this in the prompt??? Hell no"). Removed. Development history must never ship
    inside the product; the prompt already instructs the model to reason only from the numbers
    given, so explaining an absent metric added nothing and dated the prompt.
  - Owner rejected date-stamped annotations scattered across the repo ("if we use change logs,
    we use them in one place, not randomly on any document or file. This is highly
    unprofessional"). 58 such annotations across 17 files were removed in this branch, which is
    why `scope_paths` is wide: the sweep touches every file the previous branches stamped.
    **Code and docs now describe the current state only**; history lives in git, this contract,
    the review record and the handover. Reasoning is kept only where it stops someone undoing a
    deliberate decision, and even there without a date.
    **One deliberate exception: `supabase/migrations/013_net_cash.sql` keeps its dates and is
    NOT in this branch.** It is already applied, and `apply_supabase_migrations.py` tracks
    migrations by filename with no checksum, so an edit could never reach the database. Editing
    it would only make the repo describe a schema comment that differs from the live one.
    Applied migrations are immutable. A future sweep must skip it rather than "finish the job".
  - The `INPUT_HASH_VERSION` comment was rewritten from a narrative of which bump happened when
    into a description of what the constant does and the one case it does not cover (a failed
    Haiku call keeps the new hash without new prose).
  - A test asserted the literal phrase "context only" appeared in the prompt. It now pins the
    DIRECTION the growth note states instead, so wording can change without breaking the test
    while the meaning stays covered.
