# Task contract
> DISPOSABLE. **Owns:** THIS task's objective, `scope_paths`, reserved decisions and
> `done_when`.
> **Never:** anything that outlives the task. Overwritten by the next task.

objective: README product-first (owner's portfolio order; no issue). A visitor reads what the
  app is and why before any setup instructions.

scope_paths:
  - README.md
  - .claude/active_work.md
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch

decisions_reserved: settled by the owner in-thread before implementation (all five, with
  the copy as proposed) --
  1. Move "Getting started" below "Stack", text unchanged.
  2. Architecture diagram: add node "Supabase Storage / keeps every run's raw inputs" after
     "Fetch & save the raw numbers".
  3. Design decisions: new bullet "Raw inputs are archived, not just the results." with the
     proposed text.
  4. Group Project layout, Standards and Project conventions under "## For contributors".
  5. Replace "Every PR must pass `ci-validate`" with "Every merge request must pass the
     `validate` stage in GitLab CI".
  Unchanged by decision: headline, "About this project", badges, media, the GitLab project
  description and topics; the credentials table (issue #32).

known_limits: none.

regression_checklist:
  - Every section present before the change is still present, with unchanged text except
    items 2, 3 and 5.
  - The Mermaid block still parses (node ids unique, labels quoted).

done_when:
  - README order: headline, badges, demo, media, Architecture, Highlights, Design decisions,
    Stack, Getting started, For contributors.
  - Items 2, 3 and 5 carry exactly the approved copy; the diagram renders on GitLab.
  - Em-dash and pre-commit checks pass; review cycle run; MR opened. Not merged.

amendments:
