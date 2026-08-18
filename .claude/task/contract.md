# Task contract

objective: Fix agent-setup drift found during this session's guardrail audit — force-load
  the working agreement, pin the dbt-mcp server version, and repair active_work.md's
  SessionStart-injection-cap overflow and stale merged-slice status — on its own branch,
  separate from product work.

scope_paths:
  - CLAUDE.md
  - .mcp.json
  - .claude/active_work.md
  - docs/handover_2026-08-18.md

decisions_reserved:
  - Every in-repo change in this diff is a mechanical fix to an already-existing
    mechanism: an `@`-import of a doc that was already referenced by pointer, a version
    pin on an already-configured MCP server, and a trim/correction of a handover doc's
    own prose to match actual git state. No new dependency, service, lifecycle hook, or
    product/UX decision is introduced BY THIS DIFF.
  - One owner-level decision this diff *documents but does not itself make*: registering
    three previously-copied-but-unwired hooks (`commit_review_gate.py`, `pre_push_gate.py`,
    `handover_in.py`) into the GLOBAL `~/.claude/settings.json`, plus bumping
    `handover_in.py`'s `MAX_BYTES` 16000→32000. This is a new-lifecycle-hook-activation,
    global-blast-radius change per `.claude/working-agreement.md` §6, and it is genuinely
    outside this repo's git history (user-global config, not project config, so no diff
    exists for a reviewer to inspect). It was explicitly requested and authorized by the
    owner, action-by-action, in this session's own conversation — not silently decided by
    the agent — but that authorization record lives in the chat transcript, not in a
    repo-tracked artifact. `.claude/active_work.md`'s Context/open items section narrates
    this as already-done fact because it already happened, with sign-off, before this
    branch's contract was written; it is out of `scope_paths` because it touches no file
    under this repo.

done_when:
  - The 4 files are committed on `chore/agent-setup-hygiene` with a passing scope-auditor
    + cto-reviewer review for this diff.

amendments:
  - 2026-08-18 — created fresh for this hygiene task; not derived from the product task
    contract for Slice 5b/6 (this work is infra/tooling, orthogonal to that task, per the
    existing precedent of `chore/migrate-to-gitlab` being tracked separately from product
    slices).
  - 2026-08-18 — round 1 (scope-auditor + cto-reviewer): both FAIL. scope-auditor: the
    global `~/.claude/settings.json` hook-registration change was narrated in
    `active_work.md` with no `decisions_reserved` acknowledgment or authority record;
    `docs/handover_2026-08-18.md` was referenced but untracked/unstaged. cto-reviewer:
    same untracked-file gap, plus the archive doc's header wrongly stated the injection
    cap as "16KB" when the live hook is actually 32000 (two dormant plugin-source copies
    still say 16000). Fixed: `decisions_reserved` amended to name and authorize the
    global-hook action explicitly; `docs/handover_2026-08-18.md` staged for real; header
    reworded to state 16000 was the cap "at the time the overflow was diagnosed" and note
    the raise to 32000 plus the dormant-copy drift risk (new bullet added to
    `active_work.md`'s Context/open items).
  - 2026-08-18 — round 2: cto-reviewer PASS. scope-auditor FAIL: `active_work.md`'s
    Current-task section claimed the merged Router/health-verdict/Haiku-read work "are in
    production," contradicted by the same file's own Infra section (Streamlit deploy path
    unresolved, CI/CD variables unverified). Fixed: reworded to "are complete and merged,
    code-wise. Whether they're actually live for real users is a separate, unconfirmed
    question."
  - 2026-08-18 — round 3: scope-auditor + cto-reviewer both PASS against the final staged
    diff (hash `6e0a116fae7734cab349a286914c52665934a636e22c86ac511164a53efddeaf`).
