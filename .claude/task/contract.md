# Task contract
> DISPOSABLE. **Owns:** THIS task's objective, `scope_paths`, reserved decisions and
> `done_when`.
> **Never:** anything that outlives the task. Overwritten by the next task.

objective: Phase 6 (the last phase) of the owner-approved six-phase repo-cleanup plan
  (`C:\Users\Rami\.claude\plans\spicy-frolicking-bachman.md`): documentation architecture.
  9 items in the plan; every one checked against current state first (the pattern every
  prior phase has hit at least once) -- 2 turned out already done, 1 partially stale.

  1. **Delete `docs/handover_2026-05-24.md`.** Its own stated delete condition ("delete or
     archive this file once CI is green and docs are updated," line 276) has been true for
     months. Checked `docs/handover_2026-08-18.md`'s "deliberately left alone" note first
     (line 62) -- that was about not editing its GitHub-era content during a docs sweep, not
     a decision to keep the file forever; no conflict with deleting it now.
  2. **Fix `docs/handover_2026-09-03.md`'s self-contradiction.** The correction already
     exists in the file's own preamble (lines 10-15) but a reader jumping straight to
     "## Step 3: sector-calibrated verdict thresholds" (line 1668) would never see it. Added
     a short note directly above that heading, without rewriting the archived content itself.
  3. Accretion-pattern process note -- not a file edit, per the plan; skipped.
  4. **`docs/metric_layer.md`'s Phase 2 TODO, corrected not deleted wholesale.** Verified:
     `scripts/metric_formulas.py` doesn't exist (done), `audit_mart_vs_yfinance.py` already
     rebuilds via dbt (done), and the "strict model->catalogue introspection guard" idea is
     superseded by the doc's own already-existing "Why the drift guard is in Python" section
     -- all three struck. But "folding the value-aware label/gloss variants (net-cash,
     annual-basis) into the catalogue" is NOT done: `frontend/card_copy.py:228` still
     hardcodes a value-aware branch outside the catalogue. Kept, as its own live TODO.
  5. **Removed `docs/metric_audit.md`'s "Decision log" table.** Confirmed wrong as the plan
     states: its `forward_pe` row says "Keep `info_forward_pe`; monitor," but
     `docs/data_contract.md:606` documents it as dropped from the catalogue entirely,
     superseded. Rest of the file (the runbook) is untouched, still accurate.
  6. **Deleted `docs/ingest_coverage_notes.md` and `docs/intl-quarterly-row-labels.md`** --
     owner decision (AskUserQuestion this session): delete, not re-verify. Confirmed their
     findings are duplicated in `docs/data_contract.md`'s own coalesce/fallback documentation
     (net-debt coalesce at lines 71-73/223-224; quarterly operating-profit fallback at lines
     112-115/217-220) before asking, so the recommendation wasn't a guess.
  7. **Consolidated the CI/CD variables table.** `docs/supabase_setup.md`'s table (6 rows)
     was missing `ANTHROPIC_API_KEY`, present in `docs/operations_guide.md`'s copy (7 rows).
     Added the missing row to `supabase_setup.md` (the file whose job this is per its own
     scope line), replaced `operations_guide.md`'s table with a pointer.
  8. **Three small fixes, one already done.** `CLAUDE.md`'s em-dash rule already links to
     `engineering_standards.md` §1.2/§1.3 (added by an earlier phase, not this one) --
     nothing to do. `docs/development_workflow.md`'s dangling "see the migration handover"
     (line 25) now names `docs/handover_2026-08-18.md` specifically (confirmed it's the one
     documenting "trap 9," the branch-protection-ordering issue, at line 66 there).
     `.claude/working-agreement.md` §2 cited `CONTRACT_TEMPLATE.md`/`REVIEW_TEMPLATE.md`,
     neither of which exists in this repo (confirmed via `find`) -- removed the citations
     rather than inventing new template files this repo has never needed (five phases' worth
     of contracts/reviews this session alone show the working-agreement's own prose already
     specifies the shape without a separate template).
  **Repo-wide grep after the 3 deletions (per working-agreement §2: grep for the claim, not
  just the file named) found 2 live dangling references** neither the plan nor the initial
  scope caught: `docs/data_contract.md:218` cited the now-deleted `intl-quarterly-row-labels.md`
  for a fact the same paragraph already states inline -- citation stripped, fact kept.
  `docs/intl-balance-sheet-row-labels.md:7` (a live, kept sibling doc) linked directly to the
  deleted file -- redirected to `data_contract.md`'s own coverage of the same mechanism.
  9. **`CLAUDE.md`'s doc index.** Already complete and current (rebuilt in Phase 2, kept
     current by `check_docs_indexed.py` on every commit since) -- this task only removes the
     3 entries for deleted files, no rebuild needed.

scope_paths:
  - docs/handover_2026-05-24.md
  - docs/handover_2026-09-03.md
  - docs/metric_layer.md
  - docs/metric_audit.md
  - docs/ingest_coverage_notes.md
  - docs/intl-quarterly-row-labels.md
  - docs/intl-balance-sheet-row-labels.md
  - docs/data_contract.md
  - docs/supabase_setup.md
  - docs/operations_guide.md
  - docs/development_workflow.md
  - .claude/working-agreement.md
  - CLAUDE.md
  - docs/context_budget.yml
  - .claude/active_work.md
  - .claude/task/contract.md
  - .claude/task/review.md

decisions_reserved: archive-vs-reverify for the 2 coverage docs (item 6) -- ANSWERED this
  session via AskUserQuestion (delete both). The working-agreement.md template-citation fix
  (item 8) is engineering judgment (remove a dangling reference to files that never existed
  here, vs. inventing new ones this repo has never needed), not a product/mechanism decision,
  but called out explicitly since the plan gave two options and this picks one.

done_when:
  - `docs/handover_2026-05-24.md`, `docs/ingest_coverage_notes.md`,
    `docs/intl-quarterly-row-labels.md` deleted; `CLAUDE.md`'s doc index has no entry for any
    of the three.
  - `docs/handover_2026-09-03.md`'s "## Step 3" section has a correction note directly above
    it; the file's historical content below is otherwise untouched (this is an archive, not
    rewritten).
  - `docs/metric_layer.md`'s Phase 2 TODO states only the genuinely-open item (label/gloss
    variant folding); the 3 done/superseded items are gone.
  - `docs/metric_audit.md` has no "Decision log" section; the runbook content is unchanged.
  - `docs/supabase_setup.md`'s CI/CD variables table includes `ANTHROPIC_API_KEY`;
    `docs/operations_guide.md`'s own copy is replaced by a pointer to it.
  - `docs/development_workflow.md:25` names `docs/handover_2026-08-18.md` specifically.
  - `.claude/working-agreement.md` no longer cites `CONTRACT_TEMPLATE.md`/`REVIEW_TEMPLATE.md`.
  - Repo-wide grep for every deleted filename finds no live (non-archive) reference left
    dangling.
  - `python scripts/check_docs_indexed.py`, `check_context_budget.py`,
    `check_no_narrative_dates.py`, `check_no_em_dash.py` all pass.
  - `pytest tests/ -q` green, no regression (this is a docs-only task; no new tests expected).

impact_map: docs-only change; no code, schema, or CI behavior change. `CLAUDE.md`'s doc
  index: -3 entries. Net deletion of 3 files. No dbt/frontend/ingestion files touched.
