# Review

diff_sha256: c1bc1f029b6bc278c6f77d9d3dfea9ac0fb398159de8ab0e31d877bfa28a04ca

Three review rounds. Required reviewers per routing (`.claude/review_routing.json`):
scope-auditor (always), cto-reviewer (`frontend/*`, `tests/*`). No dbt or `docs/data_contract.md`
file in this diff, so analytics-engineer-reviewer and equity-analyst-reviewer are not required.

**Reviewer dispatch:** the plugin's reviewer agent types are not registered as dispatchable in
this session, so each ran as a general-purpose agent instructed to read its own role file
verbatim first. Cold, blinded, read-only input; the staged index was frozen to a patch file and
sha256 before every dispatch and never moved while reviewers were running.

**Final verdicts (round 3, the commit gate):** scope-auditor PASS, cto-reviewer PASS.

## What this is

Two small, already-diagnosed UI bugs from the row-tap-target investigation (MR !67), surfaced
to the owner as a "what's next" recommendation once the click-latency work landed, confirmed
with a plain "yes":

1. **Market filter dropdown offered markets with zero companies.** `frontend/markets.py`'s
   `MARKET_DISPLAY_NAMES` is a static 9-market dict; `explore_filters.market_filter_options()`
   listed every entry regardless of whether that market had any eligible companies exported yet
   (4 of the 9 were onboarded but the pipeline hadn't run for them since). Fixed:
   `market_filter_options()` now takes the live `cards` list and only includes a market with at
   least one eligible card, preserving the registry-ingest ordering among the ones shown, with a
   self-healing session-state guard mirroring the existing `explore_sector` pattern.
2. **Filters/stats stayed visible on the focus card.** `_render_explore_filters()` and the
   "remaining match your filters" portion of `_render_scope_stats()` ran unconditionally on the
   Discover tab regardless of focus state. Fixed: both now skip when a card is focused,
   `{saved} saved` still renders regardless, matching Saved's own already-established behavior.

Live-verified at both desktop and (after round 1's finding) an actual 480x900 mobile viewport.

## Round-by-round findings and fixes

**Round 1**: scope-auditor FAILED on two points: (a) this diff is a Discover-chrome interaction
change, so `docs/working_agreement.md`'s UX PR gate applies unconditionally, not only when a
product decision is involved -- the original contract only addressed the working agreement's
separate decision-rights question (§6). Fixed: the contract now walks through all five gate
items explicitly, including a `north_star.md` check (the Browse row already says the focus view
uses "the same layout Saved's focus view already uses," and Saved has no Filters row, so this
change moves Discover INTO alignment, not away from it). (b) The new 480px smoke-checklist rows
this diff itself added to `docs/ui/discover_header.md` were authored without ever being
exercised at 480px -- only desktop-width accessibility-tree checks had been done. Fixed:
actually re-verified at a 480x900 viewport -- no horizontal scroll on the list or focus view,
Filters row genuinely absent with no leftover gap (screenshot-confirmed), Save/Not now
reachable, "Back to list" restores cleanly. cto-reviewer PASSED round 1 cleanly, independently
tracing the session-state guard's correctness and every branch of the new `discover_focused`
condition.

**Round 2**: scope-auditor PASSED, independently re-verifying the north_star reasoning against
`docs/ui/saved_list.md`'s own wireframe (confirmed Saved's focus view genuinely has no Filters
row) and re-running the full suite fresh. Noted, not as a FAIL basis, an edge case: if the
Discover pool ever became completely empty while a card was still focused (not currently
reachable via Save/Skip/filter-change, which all clear `discover_focus_key`), the pre-existing
empty-pool message would show while this diff's own fix hides the Filters control it points to.
Also noted it could not reproduce the 480px live verification itself (no Supabase credentials in
its review environment) and assessed via code/CSS reasoning instead, finding nothing that
contradicted the claim. cto-reviewer PASSED, confirming no stale caller of the old
`market_filter_options()` signature remains anywhere in the repo.

**Round 3**: the edge case was recorded in `.claude/active_work.md` for the owner's future
awareness, explicitly not fixed (low likelihood, not a scope or decision-rights issue). Both
reviewers PASSED, re-confirming the note's technical accuracy against the actual code
(`_render_discover_tab`'s empty-pool early-return firing before the focus-key self-heal),
re-running `pytest` fresh (435 passed), and re-checking scope/decisions_reserved/the UX gate
account are all still accurate.

## scope-auditor (round 3, final)
VERDICT: PASS
risks_checked:
- Round-2 edge-case note's technical accuracy verified directly against `_render_discover_tab`:
  the empty-pool early-return fires before the focus-key self-heal, and all three actual paths
  to an empty pool today (Save, Not now, filter change) clear `discover_focus_key`
  unconditionally, so the scenario genuinely requires an out-of-band trigger.
- Scope: exactly six touched files, all inside `scope_paths`; no silent widening.
- `pytest` re-run independently: 435 passed, matching `done_when` exactly.
- Em/en-dash rule: zero matches on any added line across the whole patch.
- UX PR gate account cross-checked against source, not just the contract's own claim:
  `north_star.md`'s Browse row verbatim-matches the claimed quote; `_render_saved_tab` confirmed
  to never call anything Filters-row-equivalent. `docs/ui/discover_header.md` read in full: no
  stale claim left implying Filters/stats always show regardless of focus.
- `impact_map`'s "Saved and Search untouched" claim verified directly: neither tab's render
  function calls `_render_explore_filters` or the changed `show_remaining` logic.
- `decisions_reserved: none` re-audited: both changes are bug fixes, not new product content;
  the owner's "yes" confirmation is recorded in `active_work.md`, not left only in chat.

## cto-reviewer (round 3, final)
VERDICT: PASS
risks_checked:
- New mechanism / boring technology: `market_filter_options()` mirrors the existing
  `sectors_for_market()` pattern -- pure in-memory filtering over already-loaded data, no new
  dependency, service, or workflow step.
- Cost: no additional Supabase query volume; the focused-card branch now skips
  `_discover_pool(client)` entirely, reducing per-render cost, not raising it.
- Re-run/interruption safety: `market_filter_options(cards)` is a pure function, safe under
  Streamlit's rerun-on-every-interaction model; the new self-healing reset is idempotent and
  mirrors the pre-existing `explore_sector` pattern.
- Guard integrity: only process/handover artifacts and the two frontend files plus their tests
  changed -- no hooks, CI config, or dependency files touched.
- Verified independently: `pytest` 435 passed; zero em/en dash on any added line.
