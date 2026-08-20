# Task contract

objective: Fix agent-setup drift found during this session's guardrail audit — force-load
  the working agreement, pin the dbt-mcp server version, repair active_work.md's
  SessionStart-injection-cap overflow and stale merged-slice status, wire the review
  gate + pre-push checklist + handover injection hooks PROJECT-SCOPED (superseding a
  reverted global attempt — see amendments), and harden `review_routing.json` itself with
  4 guard-path routes modeled on football-data-pipeline's more mature routing (the owner
  asked directly for this after seeing that sibling project's routing catch a class of
  gap this repo's didn't) — on its own branch, separate from product work.

scope_paths:
  - CLAUDE.md
  - .mcp.json
  - .claude/active_work.md
  - docs/handover_2026-08-18.md
  - .claude/settings.json
  - .claude/review_routing.json

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
  - **This commit's own scope, explicitly bounded:** port ROUTING-CONFIG improvements only
    (4 new `paths` entries, all using reviewer roles this repo already has — cto-reviewer),
    modeled on football-data-pipeline's routing. Explicitly NOT ported: their
    `hash_exclude_paths`/`protected_override` mechanism, since that requires new logic in
    `commit_review_gate.py` itself (the shared hook currently reads only `always`, `paths`,
    `artifact_only`, `artifact_only_never` — verified by reading the script), which is a
    bigger, code-level "new mechanism" decision, not a config tweak. Also not ported: their
    `platform-reviewer`/`bi-analyst-reviewer` role split — introducing a new reviewer role
    that doesn't exist in this repo's `agents/` dir is out of scope for a routing-only
    change. Flagged to the owner as a separate, larger option; not decided here.

done_when:
  - The 6 files are committed on `chore/agent-setup-hygiene` with a passing scope-auditor
    + cto-reviewer review for this diff (`.claude/review_routing.json`'s new
    self-referential rule means editing it now requires cto-reviewer too, on top of the
    always-on scope-auditor).

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
  - 2026-08-18 — round 7 (new commit, hardening `review_routing.json` with 4 guard-path
    entries modeled on football-data-pipeline's routing, at the owner's direct request):
    scope-auditor + cto-reviewer both FAIL, independently, on the same root issue —
    rationale ported from the sibling repo without verifying it holds here. (1)
    `.claude/agents/*`'s comment claimed it protects "the adversary" (cto-reviewer,
    scope-auditor, etc.); verified false — this repo's `.claude/agents/` contains only
    `equity-analyst-reviewer.md`, the other four roles live entirely outside the repo in
    the dbt-agent-kit plugin's `agents/` dir, invisible to any repo-scoped gate. (2) the
    self-referential `review_routing.json` route claimed a same-commit weaken-and-exploit
    gets "caught by the reviewer it's trying to route around"; verified false —
    `commit_review_gate.py` reads the file from its current staged state with no baseline
    pinning, so a commit that weakens a rule is evaluated under the already-weakened
    rules. Fixed: `_comment_guard_paths` rewritten to state both limitations honestly
    instead of the ported claims — the rules themselves are unchanged (still real,
    still worth having), only the documentation of what they actually accomplish.
  - 2026-08-18 — round 8: cto-reviewer PASS (re-verified both round-7 facts against the
    real hook/filesystem, held). scope-auditor FAIL: the rewritten comment's own opening
    sentence claimed the ported-claims problem was "corrected twice by review... both
    rounds caught claims" — but at the moment that sentence was written, only round 7 had
    happened; this round (8) didn't exist yet, so the claim asserted a review outcome
    that hadn't occurred. Same self-referential-drift defect class as rounds 1, 2, and 5,
    reintroduced inside the very text written to fix a different instance of it. Fixed:
    reworded to "corrected by review before merge -- the first review round caught two
    claims... both scope-auditor and cto-reviewer failing independently in that same
    round" — accurate to what round 7 actually was, no forward-looking claim about rounds
    that hadn't happened yet.
  - 2026-08-18 — round 9: scope-auditor + cto-reviewer both PASS against the final staged
    diff (hash `1bd49a48a58a2908008d393eba16028c2c9f45e0e034a90eb8f7fa8b79757998`), every
    factual claim in `_comment_guard_paths` independently re-verified against the live
    filesystem and hook source, not re-read as prose.
