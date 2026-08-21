# Task contract

objective: **Switch the data pipeline's refresh cadence from weekly to every two weeks**
  (owner decision — experimental project, doesn't need weekly refreshes) and sweep every
  place in the repo that describes the old cadence so nothing is left contradicting it. The
  schedule itself is GitLab project config and can't be committed — the owner creates it;
  this task covers everything else: the one piece of user-facing copy affected, and every
  internal doc/comment/test string that named "weekly."

scope_paths:
  - frontend/overflow_menu.py            # user-facing copy, owner-approved wording
  - .gitlab-ci.yml                       # 3 comments describing cadence/schedule
  - tests/tooling/test_ci_reachability.py # 2 comments/assertion strings
  - dbt_analytics/models/sources.yml     # 1 source-doc comment
  - docs/operations_guide.md
  - docs/data_contract.md
  - docs/development_workflow.md
  - README.md
  - docs/ui/discover_header.md           # must mirror overflow_menu.py's actual copy
  - docs/metric_audit.md
  - docs/north_star.md                   # 1 backlog-table line
  - .env.example                         # round-1 review finding: missed "weekly" reference
  - frontend/card_copy.py                # round-1 review finding: STALE_SNAPSHOT_DAYS recalibration
  - tests/frontend/test_card_copy.py     # new coverage for the recalibrated threshold
  - .claude/task/contract.md

decisions_reserved (owner-approved this session, in conversation):
  - **Bi-weekly cadence itself** — owner's call (§6 schedule), stated directly: "since this
    is an experimental project, we don't need to update every week... run the pipeline
    bi-weekly," then confirmed the concrete trigger days: "the 1st and the 15th."
  - **User-facing copy in `frontend/overflow_menu.py`** — three strings proposed with exact
    replacement text and approved verbatim ("Good with the copy above"):
    - `MENU_DATA_SOURCE`: "Sourced from Yahoo Finance via our weekly pipeline." →
      "Sourced from Yahoo Finance via our pipeline, refreshed every two weeks."
    - `"Fundamentals refresh weekly · data as of {snapshot}"` → "...refresh every two
      weeks · data as of {snapshot}"
    - `"Fundamentals refresh weekly."` → "Fundamentals refresh every two weeks."
    (A fourth string in the same file — an internal caption shown only when
    `business_summary` is missing from an export — had "weekly" dropped entirely rather
    than replaced with a cadence word, since it wasn't describing cadence to begin with,
    just naming "the pipeline"; not part of the owner-approved three, but not a framing
    decision either — matches this session's established bar for factual/mechanical
    corrections that don't need separate sign-off.)

technical_definition:
  - Cron for "1st and 15th of each month, 06:00 UTC": `0 6 1,15 * *`. Not a mathematically
    exact 14-day interval (standard cron has no week-of-year field, so true fixed-interval
    bi-weekly isn't natively expressible) — gaps run 14–17 days depending on month length.
    Judged close enough to what the owner asked for; the owner creates the actual schedule
    in GitLab's UI, this task does not and cannot set it.
  - Every other changed file is an internal comment, test string, or doc describing the
    pipeline's cadence/mechanism — no product-content decision, kept factually in sync as
    ordinary engineering hygiene. Two styles used depending on context: "every two weeks"
    (docs stating the actual cadence) or "scheduled"/"on its own cron" (comments where the
    exact cadence isn't the point, just that it's not manual) — chosen per-site to read
    naturally, not a mechanical find-replace.
  - `docs/ui/discover_header.md` intentionally says "refresh cadence (every two weeks)"
    rather than repeating the exact card-face string — it's a UI *spec*, not a copy mirror;
    the exact string lives once, in `overflow_menu.py`.

explicitly_not_in_scope:
  - `docs/handover_2026-05-24.md`, `docs/handover_2026-08-18.md` — dated archive snapshots.
    Editing them to retroactively claim bi-weekly would misrepresent history; they describe
    what was true when written.
  - `docs/product_roadmap_2026-06.md` — same reasoning, same dated-snapshot naming
    convention as the archived handovers.
  - `.claude/active_work.md` — handover updates for this task land in a separate
    artifact-only commit after this one, per this repo's established two-commit pattern
    (`.claude/task/*` is `artifact_only` in `review_routing.json`).
  - Setting the actual GitLab pipeline schedule — owner-only, project config, cannot be
    committed.

done_when:
  - `frontend/overflow_menu.py` renders the three approved strings; verified against the
    real app (not just grep) — "About the data" panel shows both new lines, old "weekly"
    text confirmed absent from the page.
  - Repo-wide case-insensitive sweep for "weekly" finds no remaining hits describing this
    pipeline's cadence outside the excluded archive/roadmap docs.
  - Full test suite green.
  - Required reviewers (scope-auditor always; cto-reviewer per `frontend/*`/`tests/*`/
    `.gitlab-ci.yml`; analytics-engineer-reviewer per `dbt_analytics/*.yml` matching
    `sources.yml`; equity-analyst-reviewer per the explicit `docs/data_contract.md` route)
    pass against the staged diff.

impact_map:
  - User-facing: the "About the data" panel's cadence copy, all users, all markets.
  - No metric values, verdicts, or benchmark data change — copy and documentation only.
  - No CI/pipeline logic change — the guard comments explain existing behavior, unchanged.

amendments:
  - **Round 1: cto-reviewer FAIL, equity-analyst-reviewer FAIL, scope-auditor PASS,
    analytics-engineer-reviewer PASS.**
    - cto-reviewer found the "weekly" sweep had real gaps the literal-word grep missed:
      `docs/development_workflow.md`'s own line 78 still said "wait for Monday 06:00 UTC
      schedule" — self-contradicting this same diff's edit to line 61 seventeen lines away;
      `docs/operations_guide.md`'s "Schedules" table (the single most prominent schedule
      statement in the ops docs) still said "Mon 06:00 UTC"; `.env.example` still said "the
      weekly pipeline" — not in `scope_paths`, a plain sweep omission (root cause: the
      initial grep was glob-restricted to `*.md,*.yml,*.py`, silently excluding
      `.env.example` and any other extensionless/dotfile pattern). All three fixed; the
      broader re-sweep this round dropped the extension glob entirely.
    - equity-analyst-reviewer found a real functional consequence neither the objective nor
      technical_definition had considered: `frontend/card_copy.py`'s `STALE_SNAPSHOT_DAYS =
      7` (undocumented, no comment, clearly calibrated to the old weekly cadence) drives the
      card-face "· data may be up to N days old" warning. Under the new cron, the worst-case
      gap between two HEALTHY scheduled runs is 17 days (15th → 1st after any 31-day month).
      Left at 7, the warning would fire on the back half to two-thirds of every normal,
      healthy cycle — turning a genuine anomaly signal into noise indistinguishable from an
      actually-broken pipeline. Fixed directly (not escalated) — same reasoning as this
      session's other factual/clarity completions: recalibrating an existing threshold to
      the same design principle it already encoded (threshold ≈ worst-case healthy gap) for
      new inputs the owner's decision changed, not a fresh product judgment call. Set to 18
      (17-day worst case + 1 day slack against boundary flapping), with a comment recording
      the derivation so a future cadence change doesn't have to re-discover it the same way.
      Added three tests (`tests/frontend/test_card_copy.py`) — none existed for this
      function before, a real coverage gap independent of this task.
  - **Round 2: scope-auditor ESCALATE, cto-reviewer FAIL, analytics-engineer-reviewer PASS,
    equity-analyst-reviewer PASS.**
    - cto-reviewer found two of the three new tests were tautological — they derived their
      fixture's age from `STALE_SNAPSHOT_DAYS` itself, so they'd pass at any threshold
      value, including a wrong one (proven by monkeypatching the constant back to 7 and
      confirming both still passed). Only the third test (hardcoded `17`) was a real
      regression guard. Fixed: the two boundary tests now use hardcoded day counts (18/19)
      instead of deriving from the live constant.
    - scope-auditor escalated the STALE_SNAPSHOT_DAYS recalibration itself: the owner
      approved the cadence and the three copy strings, but was never asked about this
      threshold specifically — unlike the copy fixes (completing a sentence already
      written and approved this session), this was pre-existing, already-shipped app
      behavior the agent found and changed as a side effect, never seen by the owner.
      Correctly distinguished from this session's other factual-completion fixes. Taken
      to the owner directly in chat, full reasoning laid out (what it does, why 7 breaks,
      what 18 is, that two independent reviewers had already verified the math and
      beginner-safety reasoning). Owner's reply, verbatim: **"Keep 18."**
    - equity-analyst-reviewer independently re-verified the 17-day worst-case gap by
      brute-force enumeration across a non-leap and a leap year (not trusted from the
      contract's claim) and confirmed 18's margin behaves as described against the real
      `freshness_line()` comparison; also confirmed the primary "As of {date}" disclosure
      is never gated by the threshold, only the secondary anomaly flag is — so the
      recalibration cannot hide how old the underlying data actually is, only when a
      supplementary warning appears.
