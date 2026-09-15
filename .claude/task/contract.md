# Task contract
> DISPOSABLE. **Owns:** THIS task's objective, `scope_paths`, reserved decisions and
> `done_when`.
> **Never:** anything that outlives the task. Overwritten by the next task.

objective: Phase 3 of the owner-approved six-phase repo-cleanup plan
  (`C:\Users\Rami\.claude\plans\spicy-frolicking-bachman.md`): GitLab Issues/Milestones
  replace doc-based roadmap and backlog tracking.

  GitLab side (not committed, done via `glab`): create 2 project Milestones ("1 · Discover
  depth", "2 · Data quality"); file 7 issues (What exactly / Why shape, football-data-pipeline
  pattern) covering the 3 genuinely-open `docs/backlog/*.md` items plus the 4 still-open
  one-line items from `north_star.md`'s Phase 2 table, assigned to the matching milestone.
  Both the milestone set and the file-vs-drop call on the 4 one-liners were owner decisions
  (AskUserQuestion, this session) -- not defaulted.

  Repo side: delete `docs/product_roadmap_2026-06.md` and the 6 already-resolved/migrated
  `docs/backlog/*.md` files; reword `north_star.md`'s Phase 2 table to point at the
  milestone; point `.claude/working-agreement.md` §2 at issues (`Closes #N`/`Refs #N`
  in `objective`) instead of restating requirements inline.

  Two corrections to the plan file's literal text, found during Explore, refined again
  during owner review before implementation -- stated here so review can check the final
  shape, not just the plan file:
  1. **`gemini_verdict_feedback.md` IS deleted, per the plan -- but not by just deleting
     it.** 8 live citations by point number would have dangled (4 in `.py` files, 1 test, 2
     in `data_contract.md`; an 8th, a `.sql` comment, was missed by the first grep and caught
     by round-1 review). All 8 already carried the substantive reasoning inline -- the file
     mention was decorative -- so all 8 got the citation stripped, reasoning kept, no new
     content added. The one arguably-unique piece (point 9, why thresholds aren't
     sector/size-calibrated) is already covered by `data_contract.md`'s existing "declined
     twice" paragraph. File deleted outright, verified safe by grep rather than assumed.
  2. **`product_roadmap_2026-06.md` is deleted, content checked against every DURABLE doc's
     `Owns:` header first, not moved wholesale.** Owner pushback mid-task on an earlier draft
     that would have dumped its "Premortem guardrails" into `north_star.md` unfiltered -- same
     scattering-decisions problem this cleanup exists to fix. Of 5 guardrails, 3 duplicate
     existing rules (`north_star.md`'s queue-counter line, `metric_layer.md`'s mandatory copy
     field, working-agreement §4's no-scope-creep) -- dropped as duplicates. 2 (a Streamlit
     button-label quirk, the Streamlit exit trigger) fit no doc's declared scope -- dropped,
     not homed. 1 out-of-scope line (dbt-side filters unnecessary) fit `north_star.md`'s
     existing out-of-scope list -- added. Backlog table, "Sequencing" table, and 2 stale
     scope lines dropped (superseded by milestones / already contradicted by current state).

scope_paths:
  - docs/product_roadmap_2026-06.md
  - docs/backlog/discover_metric_filters_phase2.md
  - docs/backlog/name_vs_yfinance_audit_guard.md
  - docs/backlog/discover_saved_search_ux_findings.md
  - docs/backlog/discover_first_time_default.md
  - docs/backlog/discover_list_performance.md
  - docs/backlog/landing_onboarding_rework.md
  - docs/backlog/gemini_verdict_feedback.md
  - docs/north_star.md
  - docs/ui/discover_list.md
  - docs/data_contract.md
  - frontend/card_copy.py
  - scripts/assessment_rules.py
  - tests/tooling/test_assessment_rules.py
  - dbt_analytics/models/4_intermediate/int_stock__sector_benchmarks.sql
  - scripts/check_no_narrative_dates.py
  - CLAUDE.md
  - docs/context_budget.yml
  - .claude/working-agreement.md
  - .claude/active_work.md
  - .claude/task/contract.md
  - .claude/task/review.md

decisions_reserved: milestone set and issue-filing scope for the 4 north_star one-liners --
  ANSWERED this session via AskUserQuestion (2 milestones as previewed; file all 4 as
  issues). The two plan-text corrections above are engineering judgment (grep-verified live
  references / duplicated content), not product decisions, but are called out explicitly for
  review rather than silently deviating from the approved plan file.

done_when:
  - 2 GitLab Milestones exist ("1 · Discover depth", "2 · Data quality"); 7 issues exist,
    each assigned to the correct milestone, each with a `## What exactly` task list and
    `## Why` body.
  - `docs/backlog/` no longer exists (all 7 files removed, none moved);
    `scripts/check_no_narrative_dates.py`'s own docstring no longer cites that directory or
    the now-false working-agreement.md §2 claim (round-4 cto-reviewer finding).
  - All 8 code/doc/SQL comments citing `docs/backlog/gemini_verdict_feedback.md` by point
    number (4 in `.py` files, 1 test, 2 in `data_contract.md`, 1 in a dbt SQL model, the last
    found by round-1 review, not the original grep) keep their substantive reasoning, with the
    now-dangling file citation stripped; no new content needed since `data_contract.md`'s
    existing "declined twice" paragraph already covered the one otherwise-unique point.
  - `docs/product_roadmap_2026-06.md` deleted; its still-relevant content (one out-of-scope
    line) is in `north_star.md`, checked against that doc's own `Owns:` line rather than
    moved wholesale; grep for `product_roadmap_2026-06` across the repo returns only the
    one point-in-time archive (`docs/handover_2026-05-24.md`) allowed to keep it, plus this
    task's own disposable contract/review files.
  - `docs/ui/discover_list.md`'s dangling `docs/backlog/discover_list_performance.md`
    pointer removed; the measurement fact it introduces stays inline.
  - `.claude/working-agreement.md` §2 documents linking a task's `objective` to a GitLab
    issue (`Closes #N`/`Refs #N`) when one exists.
  - `python scripts/check_docs_indexed.py`, `check_context_budget.py`,
    `check_no_narrative_dates.py`, `check_no_em_dash.py` (against staged diff) all pass.
  - `pytest tests/ -q` green, no test count regression.
  - Repo-wide grep for every deleted filename finds no live (non-archive) reference left
    dangling.

impact_map: doc + GitLab metadata change; no behavior/schema change. `frontend/card_copy.py`,
  `scripts/assessment_rules.py`, and one `dbt_analytics/models/4_intermediate` SQL model each
  lose one dangling comment citation, code/SQL otherwise byte-identical -- no dbt column,
  compute, or output changes. `CLAUDE.md`'s doc index: -1 line (roadmap), net count -1. `north_star.md`'s
  Phase 2 table (6 lines) replaced by a 2-line milestone pointer; one bullet added to its
  existing out-of-scope list. No dbt/ingestion/Supabase files touched.
