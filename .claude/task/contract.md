# Task contract

objective: Fix agent-setup drift found during this session's guardrail audit — force-load
  the working agreement, pin the dbt-mcp server version, repair active_work.md's
  SessionStart-injection-cap overflow and stale merged-slice status, and wire the review
  gate + pre-push checklist + handover injection hooks PROJECT-SCOPED (superseding a
  reverted global attempt — see amendments) — on its own branch, separate from product
  work.

scope_paths:
  - CLAUDE.md
  - .mcp.json
  - .claude/active_work.md
  - docs/handover_2026-08-18.md
  - .claude/settings.json

decisions_reserved:
  - Every in-repo change in this diff is a mechanical fix to an already-existing
    mechanism: an `@`-import of a doc that was already referenced by pointer, a version
    pin on an already-configured MCP server, a trim/correction of a handover doc's own
    prose to match actual git state, and registering three existing, unmodified hook
    scripts (`commit_review_gate.py`, `pre_push_gate.py`, `handover_in.py`, all already
    reviewed and PASSED in rounds 1-3 below when they were wired globally) into THIS
    repo's own `.claude/settings.json` instead. No new dependency, service, or
    product/UX decision is introduced BY THIS DIFF.
  - **Superseded decision, kept for the record:** rounds 1-3 (below) originally reviewed
    and passed these same three hooks wired into the GLOBAL `~/.claude/settings.json`
    (owner-authorized in-session, outside this repo's git history). That global wiring
    broke a DIFFERENT project (football-data-pipeline) — its own, differently-shaped
    `review_routing.json` (with a `hash_exclude_paths` key the global hook doesn't know
    about) meant the global `commit_review_gate.py` computed a different review hash than
    that project's own gate, causing false commit blocks there. The owner reverted the
    global wiring immediately upon discovering this and directed the fix to be
    project-scoped instead — this diff. Project-scoped wiring in `.claude/settings.json`
    carries zero cross-project blast radius by construction (it only loads when this
    repo is the active project), so the collision this diff exists to avoid cannot recur
    here regardless of what any other project does. Memory saved:
    `global-hooks-collision-risk`.
  - **Round-4 finding, resolved by direct owner decision (AskUserQuestion):** whether to
    commit `.claude/settings.json` (tracked, visible in-repo) or keep it gitignored like
    the pre-existing `.claude/settings.local.json` (which already carries an unrelated
    PowerShell-deny hook). The tracked commands reference `$HOME/.claude/hooks/*.py`, a
    machine-specific absolute path that would not resolve if this repo were cloned
    elsewhere. Owner chose **commit it (tracked)**, accepting that portability caveat in
    exchange for the wiring being visible/documented in-repo rather than invisible,
    machine-only config.

done_when:
  - The 5 files are committed on `chore/agent-setup-hygiene` with a passing scope-auditor
    review for this diff (no path in this addition matches a `cto-reviewer` route in
    `.claude/review_routing.json` — `.claude/settings.json` isn't listed there, unlike
    football-data-pipeline's routing).

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
  - 2026-08-18 — round 4 (new commit, adding `.claude/settings.json` to re-wire the same
    3 hooks project-scoped after the global revert): scope-auditor FAIL. Two findings:
    (1) `active_work.md` still said the hooks were "wired globally," contradicting this
    diff's own premise — fixed, reworded to describe the project-scoped wiring and the
    global-revert history. (2) the contract's `decisions_reserved` authorized *where* the
    hooks fire (global vs. project) but never addressed *whether to track the wiring file
    in git at all* — a distinct axis from what rounds 1-3 authorized. Escalated to the
    owner directly (AskUserQuestion) rather than assumed; owner chose to commit it
    (see the new decisions_reserved bullet above).
  - 2026-08-18 — round 5: scope-auditor FAIL. `active_work.md`'s Next-concrete-actions
    item 4 said the branch had "Two commits," undercounting the real history (a third,
    `9de7726`, had already landed and this diff was about to add a fourth) — the same
    self-referential-drift defect class that failed rounds 1 and 2. Fixed structurally,
    not just re-counted: removed the hardcoded commit list/hashes entirely, pointing to
    `git log chore/agent-setup-hygiene` / the MR instead, and corrected "MR not yet
    opened" to "MR #5 open."
  - 2026-08-18 — round 6: scope-auditor PASS against the final staged diff (hash
    `ff0a49bc4c82e5480c624cd4b11316d2c7ba1e3ac441422261627b36535cdfff`), independently
    verified live via `glab` (MR #5's state, plus MR #3/#4's claimed merged status).
