# Task contract
> DISPOSABLE. **Owns:** THIS task's objective, `scope_paths`, reserved decisions and
> `done_when`.
> **Never:** anything that outlives the task. Overwritten by the next task.

objective: Closes #53 -- the quality-baseline audit re-runs against identical, versioned
  criteria: criteria file, named workflow, mechanical quote check with tests, CLAUDE.md pointer.

scope_paths:
  - docs/quality_criteria.json
  - .claude/workflows/quality-baseline-audit.js
  - scripts/verify_quality_audit.py
  - tests/tooling/test_quality_audit.py
  - CLAUDE.md
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch

decisions_reserved: settled by the owner in-thread -- option 1 (criteria as a JSON file in the
  repo, the script as a named workflow in `.claude/workflows/`). The criteria are the 30 the
  audit behind #45-#52 ran against, unchanged apart from dropping the session-specific
  known-issues list; the workflow reads open issues live instead. Changing a criterion needs a
  version bump and owner approval.

done_when:
  - `docs/quality_criteria.json` holds version 1: 7 areas, 30 criteria, each with id, rule and
    source; a test fails on a duplicate id or a criterion without a rule or source.
  - `.claude/workflows/quality-baseline-audit.js` reads that file by default and audits the
    same 7 areas; a test fails if the workflow, criteria and report cover different areas.
  - `scripts/verify_quality_audit.py` reports only skeptic-confirmed findings whose verbatim
    quote is at the cited file and line, and lists refuted and unverified ones separately;
    tests pin both, plus the window edges, quote order, and that a quote under 10 normalised
    characters passes only as the whole cited line; a finding with no
    skeptic verdict and an area whose auditor failed are shown as such, never as refuted or
    clean. On this session's real run it reproduces 61 reported of 64 raised.
  - The criteria content is pinned to its version by a fingerprint test.
  - CLAUDE.md points at the criteria file, the workflow and the checker.

known_limits:
  - A quote of 10 or more normalised characters matches within +-3 lines of the cited line, so
    one that appears elsewhere in the window passes; a shorter one matches only as the whole
    cited line.
  - Read-only is enforced by the agents' instructions, not by a tool allowlist; restricting the
    tools would change the setup the #45-#52 run used.
  - DOC-2 and HYG-4 also cite the owner's global CLAUDE.md, outside the repo; changing a
    criterion's source is a version 2 decision for the owner.
  - The workflow's findings depend on the auditing model; the criteria and the checks are fixed,
    the judgement is not.

regression_checklist:
  - The criteria ids and rules match the run behind #45-#52 (version 1, 30 criteria).
  - The docs-index and context-budget checks still pass.
