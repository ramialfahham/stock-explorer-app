# Task contract
> DISPOSABLE. **Owns:** THIS task's objective, `scope_paths`, reserved decisions and
> `done_when`.
> **Never:** anything that outlives the task. Overwritten by the next task.

objective: README documentation gap the owner flagged: the AI-written card read (Claude
  Haiku, `scripts/generate_assessments.py`) is a real architectural component and a
  genuine differentiator, but is completely absent from the README -- not in the
  architecture diagram, Highlights, or Stack table. Someone reading it would have no idea
  the app uses an LLM at all. Owner's direction: "worth mentioning that some AI feature is
  integrated here." Also rounds out two minor gaps found in the same review:
  `tests/`/`storage/` missing from the Project layout tree, and `streamlit_app.py`
  (the actual entry point run in Local setup step 8) / `render.yaml` not shown either.

scope_paths:
  - README.md
  - .claude/task/contract.md
  - .claude/task/review.md

decisions_reserved: none -- the owner gave the exact direction ("mention some AI feature
  is integrated") in chat; wording stays plain and proportionate to that ask, matching the
  README's own existing voice and level of detail, not a new marketing push.

done_when:
  - The architecture diagram shows the AI-read step (Claude Haiku, generating each card's
    verdict + prose read) feeding into Supabase, positioned accurately relative to the
    real pipeline order (`.gitlab-ci.yml`: dbt build -> export_to_supabase.py AND
    generate_assessments.py, both reading the same dbt-built data, writing separate
    Supabase tables).
  - The diagram's own node labels are plain-language, not internal jargon (owner:
    "non-technical people should understand what's going on") -- tool names (yfinance,
    dbt, Supabase, Claude, Streamlit, GitLab CI) stay as proper nouns, but internal terms
    like "ephemeral DuckDB", "1_staging -> 5_marts", "card marts", "data contract",
    "index-constituent fundamentals" don't appear in the diagram itself. Verified by
    actually rendering the Mermaid syntax (a local static-file check), not just
    eyeballing the text.
  - Highlights gains one bullet for the AI-written read, same density as the existing
    bullets.
  - Stack table gains a row for it.
  - Project layout tree includes `tests/`, `storage/`, `streamlit_app.py`, `render.yaml`.
  - `python scripts/check_no_em_dash.py` passes.

impact_map: README.md only. No code, no diagram-rendering dependency beyond the Mermaid
  block already there. Purely closing a real documentation gap.
