# Task contract

objective: Delete the process prose that produced eleven review rounds on MR !115, and write
  down the rule that stops it recurring.

  The export code was settled at review round 5 and never changed again. Rounds 6-11 were
  entirely findings against prose DESCRIBING that code: wrong counts, a claim corrected in one
  file and left standing in another, and twice a sentence contradicting another sentence in the
  same file. `contract.md` was 35,527 bytes, of which 25,064 (71%) was an `amendments:` section
  narrating the author's own mistakes. That section was the source of most of the errors and of
  every mirror that contradicted the docs.

  Narrative rots because nothing checks it. Git history and an MR description cannot, because
  they are append-only and never claim to describe the present.

scope_paths:
  - .claude/active_work.md
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/working-agreement.md
  - docs/supabase_setup.md
  - frontend/app.py
  - supabase/migrations/018_atomic_card_export.sql

decisions_reserved:
  - THE RULE ITSELF is a change to how this repo works, so §6 makes it the owner's. Asked
    directly ("For what do we need your prose. The prose is the problem.") and answered "do it".
    The rule adopted: prose earns its place only if it records a decision not derivable from
    code, defines something the code cannot state itself, or is machine-checked. Everything else
    goes to git and the MR description.
  - NOT DONE, FLAGGED: `CONTRACT_TEMPLATE.md` and `REVIEW_TEMPLATE.md` live in the dbt-agent-kit
    plugin, outside this repo, and still prescribe the categories being removed here. Editing
    them changes every project using the plugin and never appears in this repo's diff. Left for
    the owner to decide; this branch only changes what this repo does.
  - NOT DONE, FLAGGED: the merge guard covers `gh pr merge` only, so `glab mr merge` -- the
    command this repo would actually use -- is blocked by nothing. Closing it means editing
    `~/.claude/hooks/branch_discipline.py`, a per-machine file every project shares, so it is
    the owner's call. The working agreement now states the gap instead of overselling the guard.
  - NOT DONE, FLAGGED: `.claude/working-agreement.md` has no required reviewer in
    `review_routing.json` beyond `always`, though it governs how every agent works here.
    cto-reviewer was dispatched voluntarily for this change. Adding a routing entry is a rule
    change and was not made unilaterally, since a self-authorized scope widening was already
    flagged on the previous branch.

done_when:
  - `.claude/task/contract.md` has no `amendments:` section and no narrative of how the work
    went, and this file demonstrates that by being one.
  - `.claude/active_work.md` is materially under its 32,000-byte cap rather than 20 bytes under
    it, with every owner decision, standing rule and open item preserved.
  - Facts that were load-bearing but lived only in the deleted narrative have a home next to
    what they describe: export timing and the PostgREST schema cache in `docs/supabase_setup.md`,
    the column-list rationale in the migration itself, and the owner-approved 15-60 minute band
    for `_DECK_TTL_SECONDS` as a comment beside that constant in `frontend/app.py`.
  - `.claude/working-agreement.md` states the rule, so the next session inherits it.
  - `pytest tests/ -q` green. NOT sqlfluff: it lints `dbt_analytics/models` and
    `dbt_analytics/tests` only, so it cannot see the migration whose comment changed, and
    citing it here would manufacture belief in a gate that does not cover this diff. The
    migration comment is verified by reading it against the code it describes, which is what
    the reviewers did.

impact_map: Documentation and one SQL comment. No executable line changes, so no runtime,
  schema or CI behaviour moves. The risk is deletion, not breakage: losing a fact that had no
  other home. Mitigated by moving the load-bearing ones first and by scope-auditor checking the
  handover against what it previously carried.
