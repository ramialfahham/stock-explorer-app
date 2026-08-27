# Task contract

objective: Add an `onboard-market` skill so that an agent asked to add a market FINDS the
  activation checklist instead of improvising one. Deliberately thin: it points at
  `docs/data_contract.md` rather than restating it, and carries only what a step list cannot,
  namely the ongoing cost, the owner-only decisions, and the traps found while onboarding
  France. Phase 1 item 1b of the ingestion work.

scope_paths:
  - .claude/skills/onboard-market/SKILL.md
  - docs/development_workflow.md
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/active_work.md

impact_map:
  - No code, no data, no schema, no pipeline behaviour. One markdown file that changes what a
    future agent reads before starting.
  - No cost of any kind: nothing runs, nothing regenerates, no card or verdict moves.
  - Changes agent behaviour on a task class that has already failed once, which is the point.

decisions_reserved:
  - **The owner asked whether a skill existed for this and was told no**, then chose the
    sequencing ("you choose") while the skill itself was already agreed. Writing it is
    therefore in scope; its SHAPE is the judgement recorded below.
  - **The skill is a POINTER, not a copy, and that reverses the original plan.** France was
    done by hand specifically to learn the procedure well enough to write a skill. What the
    branch actually found is that the procedure was already written down in
    `docs/data_contract.md` and simply not read. Restating those steps here would create the
    second copy that this repo's single-source rule forbids, and would reproduce exactly the
    defect just fixed in `docs/development_workflow.md`, whose rival list had drifted into
    contradicting the canonical one. **The failure mode was discovery, not content**, so the
    skill's whole job is to make an agent find the checklist and understand what it is signing
    up for.
  - **A thin or stubbed constituent is NOT an owner decision.** The first draft filed it under
    "the owner's call" and then decided it in the next clause, contradicting the France
    contract, which classified the same `ML.PA` question as an implementation judgement with a
    defensible default. The latter is right: carry it and let eligibility drop it.
  - **`.claude/skills/*` has no routing entry**, so only scope-auditor is required for this
    change. A skill instructs every future agent on a task class, which is the same authority
    class as `.claude/agents/*` and `.claude/settings.json`, both of which route to
    cto-reviewer. cto-reviewer is therefore run voluntarily here, and the gap is flagged for
    the owner rather than fixed: adding a routing pattern is an edit to
    `.claude/review_routing.json`, which is a governance change and the owner's call.

done_when:
  - The skill triggers on the phrasings an owner would actually use ("add a market", "onboard",
    "activate", "enable") and names concrete indices so the description is recognisable.
  - It restates no checklist content. **The first draft failed this and its acceptance test did
    not notice**: the test was "zero numbered steps in the file", a formatting check that cannot
    detect duplication. The file restated four steps in prose, and the one number it restated
    was wrong, attributing the WARN-below-20 threshold to `check_eligibility_baseline.py` when
    it lives in `check_pipeline_completeness.py`. That is the drift the skill's own rationale
    predicts, arriving at birth. The real test: for each mechanic the file mentions, does
    `docs/data_contract.md` already carry it? If yes, cut it and point.
  - What survives is only what no document carries: the Wikipedia user-agent 403 and the
    positional, silently-wrong `table_index`. Both verified absent from `docs/` (the 403 hits
    there are Supabase Management API failures, an unrelated thing).
  - The failure story keeps its consequence and drops the mechanism. An earlier draft restated
    step 7's how (three FK tables, the export writing only the mart); that is cut, and only the
    what remains (an aborted export for every market, CI green), phrased as a counterfactual
    about France so a later CI job cannot falsify it. Both reviewers caught the original as the
    same drift hazard this skill exists to argue against: add a fourth FK table and the skill
    misinforms while the checklist stays right.
  - `docs/development_workflow.md` points at the skill WITHOUT naming its traps. Naming them
    there made the skill's own claim false on merge and recreated the second copy in the same
    edit that removed one.
  - The description names only indices the owner actually chose. An earlier draft listed
    OMXS 30 for Sweden, which the owner has not picked, presenting it as settled inside a file
    whose own rule is to present options and recommend rather than choose silently.
  - It states the ongoing cost per run and names the owner-only decisions, without asserting an
    unrun result as fact. France's post-run deck size is an extrapolation and is not quoted.
  - `docs/development_workflow.md` no longer plans a rival skill. It described
    `.claude/skills/stock-swipe-ingestion/SKILL.md` as future work covering the same checklist,
    which would have told the next agent to build a second overlapping copy.
  - No em dash or en dash.
