# Task contract
> DISPOSABLE. **Owns:** THIS task's objective, `scope_paths`, reserved decisions and
> `done_when`.
> **Never:** anything that outlives the task. Overwritten by the next task.

objective: Closes #45 -- durable docs state the current state only; the narrative checker covers
  every governed doc by path and an MR reference split across a line break.

scope_paths:
  - scripts/check_no_narrative_dates.py
  - tests/tooling/test_check_no_narrative_dates.py
  - docs/handover_2026-08-18.md
  - docs/handover_2026-09-03.md
  - docs/context_budget.yml
  - CLAUDE.md
  - .claude/active_work.md
  - .claude/working-agreement.md
  - .claude/agents/scope-auditor.md
  - .claude/skills/onboard-market/SKILL.md
  - docs/development_workflow.md
  - docs/data_contract.md
  - docs/operations_guide.md
  - docs/supabase_setup.md
  - docs/north_star.md
  - docs/intl-balance-sheet-row-labels.md
  - docs/ui/disclosure_pattern.md
  - docs/ui/design_system.md
  - docs/ui/discover_list.md
  - docs/ui/discover_header.md
  - docs/ui/card_metric_cell.md
  - docs/ui/saved_list.md
  - docs/ux_principles_finanz_lern_apps.md
  - docs/working_agreement.md
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch

decisions_reserved: settled by the owner in-thread, as recommended -- D1 (b): the checker scans
  every governed Markdown doc by path (docs/, docs/ui/, README, CLAUDE.md, the working agreement,
  skills, agents) plus any `> DURABLE.` doc; D2: delete both handover archives from docs/ (git
  history keeps them), move "trap 9" into development_workflow.md, drop their CLAUDE.md, budget
  and handover references; D3: fix the cited findings, their named siblings, the widened
  checker's hits, the "Slice N" labels and the same history phrasing found by a sweep.
  Round-1 amendments, owner-approved in-thread: "Slice N" labels in code comments are split to
  #55; "v2.5" version labels in governed docs are removed as history labels; the three governed
  docs outside the original scope_paths (saved_list, ux_principles, docs/working_agreement) are
  added under D3. `docs/quality_criteria.json` still names the deleted archives; changing it is
  the owner's pending criteria-v2 decision, not this task.

done_when:
  - `check_no_narrative_dates.py` scans every governed doc (paths anchored at the repo root,
    `.pytest_cache` excluded) without opting in, and flags any of its patterns split across two
    lines (joined with and without a space, so a break inside a token counts) unless the allow
    marker is on either line; tests pin each governed path, nested non-governed paths, the
    `.pytest_cache` exclusion, splits between words (MR and owner patterns) and inside tokens
    (all three patterns), and the marker on either line, and fail if either rule is removed.
  - The checker passes on the repo.
  - Findings 40-47 of #45 are fixed as proposed, with the sibling sites finding 45 names.
  - No "Slice N" or "v2.5" label remains in a governed doc, and this sweep over governed docs
    returns only the keep list below:
    `git grep -n -i -E '\b(used to|previously|no longer|has since|have since|an earlier|the old [a-z]+|first version|was (removed|dropped|replaced|retired|renamed|reverted|changed)|were (removed|dropped|replaced)|retired|replaced the|once the fix|before it was fixed|before this (column|rule) existed|gemini feedback|prior [a-z]+ attempt|v[0-9]+\.[0-9]+\b|\(dropped:|removed as redundant|moved .* now lives|corrected in review|now bands|did exactly that|originally|reintroduce)'`.
    Keep list (current behaviour or a user instruction): data_contract.md "no longer in the
    mart", "an earlier snapshot", "naming the old one", "the old market list"; operations_guide.md
    "an earlier one the same day", "no longer what ingestion produced"; supabase_setup.md "If you
    previously ran".
  - Both handover archives are gone; nothing in the repo links to them; trap 9 is stated in
    development_workflow.md.
  - Context-budget and doc-index checks pass.

known_limits:
  - Undated history prose has no reliable pattern, so the checker still cannot catch it; review
    and the quality-baseline audit's DOC-2 criterion carry that.
  - "No longer" that describes current behaviour (a ticker dropping out between runs) is kept.

regression_checklist:
  - No rewritten sentence changes what a doc says is true now.
  - The checker's Python and SQL scanning are unchanged apart from the shared excluded-directory
    set (now also `.pytest_cache`); only Markdown scope, the split-line rule and the docstring
    describing them changed.
