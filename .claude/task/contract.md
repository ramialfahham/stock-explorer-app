# Task contract

objective: Two owner-decided Saved-tab fixes, from today's product-work review:

  1. **"Clear saved" (the bulk action in the "⋯" overflow menu) has no confirmation** -- one
     click wipes every saved company (and skip history) with no undo. Owner chose: gate it
     behind a popover-style confirmation (a candidate direction already sketched in
     `docs/backlog/discover_saved_search_ux_findings.md`, not previously decided).
  2. **There is no way to remove a single saved company** -- only the all-or-nothing bulk
     clear. Owner chose: add per-item removal too, after being shown (via code, not assumed)
     that no such affordance exists anywhere in the Saved tab today.

  **A third finding changed the shape of this task, found during planning, not assumed:**
  `frontend/explore_filters.py` has its own, independent copy of "which tickers are saved"
  (`_saved_keys()`), used by `filter_pool()` to exclude saved tickers from the Discover pool --
  a pairing `docs/north_star.md` documents explicitly ("Adds ticker to Saved. Removes from
  scoped discover pool."). That copy has no concept of "unsave" reversing a save. Left unfixed,
  shipping per-item removal alone would make things worse than today: a removed ticker would
  vanish from Saved but stay excluded from Discover forever, and since Search has no Save
  action, there would be no way to ever re-save it short of clearing the entire list. Fixing
  this is a precondition for per-item removal being safe to ship, not optional scope creep --
  escalated and shown to the owner before proceeding, not decided silently.

  Both product decisions (add confirmation; add per-item removal) were made explicitly by the
  owner in-thread. The engineering shape (where the shared logic lives, the exact tie-break,
  the popover-nesting workaround, the ordering-bug fix below) was planned via this repo's
  Explore -> Plan -> Confirm cycle: one Explore pass over the actual code (not assumed), one
  Plan-agent validation pass that caught two real bugs before any code was written (see
  `decisions_reserved` and the plan-validation findings folded into `done_when` below), then
  owner sign-off on the written plan before implementation started.

scope_paths:
  - frontend/explore_filters.py (new shared helper, `filter_pool` fix, delete dead
    `_saved_keys()`)
  - frontend/app.py (`_saved_count`/`_saved_cards` delegate to the shared helper;
    `_render_saved_tab` gets the "Remove from saved" button)
  - frontend/overflow_menu.py (`render_overflow_menu`'s confirm-state logic + an ordering fix,
    see below)
  - tests/frontend/test_explore_filters.py (new tests)
  - docs/ui/saved_list.md, docs/north_star.md, docs/ui/discover_header.md,
    docs/backlog/discover_saved_search_ux_findings.md (doc updates)
  - .claude/active_work.md
  - .claude/task/contract.md
  - .claude/task/review.md

decisions_reserved: none outstanding -- both product decisions (confirmation step; per-item
  removal) and the one scope-expanding technical finding (the `explore_filters.py` fix) were
  put to the owner and approved before implementation began, not decided unilaterally.

  Two smaller engineering choices, judged agent-executable (implementation-level, not
  product/wording): no new "danger" button color for the destructive actions -- this app is
  deliberately monochrome-plus-one-gold-accent (`docs/ui/design_system.md`'s "monochrome-only
  constraint"; even the red verdict badge conveys severity via a color-less 🔴 emoji, never a
  red CSS rule), so severity comes from copy alone, not a new color that would be the first of
  its kind in this app.

  The third -- no confirmation on the per-item removal -- is NOT self-classified by analogy:
  it was written out explicitly as its own numbered section in the plan file
  (`groovy-churning-scroll.md`, section 3, "No confirmation on this one: single item, and --
  now that fix 1 is in place -- trivially re-saved from Discover if it was a mistake. This
  reasoning only holds because of fix 1; it would not hold without it.") and the owner approved
  that exact plan via `ExitPlanMode` before implementation began -- the owner read this specific
  reasoning, not just the two headline product decisions, and signed off on it. Recorded here
  because the plan file itself lives outside this repo's git history, so a cold reviewer has no
  other way to see that trail.

done_when:
  - `frontend/explore_filters.py`: new `saved_keys_with_order(interactions)` pure helper
    (latest save/unsave action per `(market_code, ticker)` wins, `>=` tie-break matching the
    tie-break `_saved_cards` already used for sort order); `filter_pool` calls it instead of
    `_saved_keys()`; `_saved_keys()` deleted (confirmed dead, not just superseded).
  - `frontend/app.py`: `_saved_count`/`_saved_cards` delegate to the shared helper instead of
    their own inline "any save ever" logic. `_render_saved_tab`'s focused-card view gets a
    plain in-flow "Remove from saved" button (`type="secondary"`, explicit key) below the card
    -- matching "<- Back to list"'s existing plain treatment in this same view, not Discover's
    fixed-to-viewport action bar (a different, unrelated treatment this view has never used).
    Handler clears `saved_focus_key` in the same click (matching how "Not now" already clears
    `discover_focus_key`), calls `append_interaction(selected, "unsave")` (same inline-call
    convention "Not now" already uses, no new wrapper function), then `st.rerun()`.
  - `frontend/overflow_menu.py`: `render_overflow_menu`'s "Clear saved" button gated behind
    `st.session_state["confirm_clear_saved"]`. Armed state shows "Clear all {N} saved
    compan{y/ies}? This can't be undone." (singular/plural handled the way `right_now_line`
    already does, not hardcoded) plus Cancel/Clear-all buttons (`type="secondary"`, explicit
    keys). **Ordering fix, found during plan validation, not optional:** `clear_interactions()`
    already ends with its own internal `st.rerun()`, which halts the rest of the script run --
    so the flag reset and `on_clear_saved()` must happen BEFORE calling `clear_interactions()`,
    not after, or the confirm prompt gets stuck reading "Clear all 0 saved companies?" on next
    open. Verified explicitly in manual testing below, not just reasoned about.
  - `tests/frontend/test_explore_filters.py`: `saved_keys_with_order` covered for never
    saved / saved once / saved-then-unsaved / saved-unsaved-saved-again (keyed on the second
    save's timestamp, not the first) / unsaved-without-ever-saving. New `filter_pool`
    regression test for save-then-unsave (ticker reappears in the pool) -- this is the test
    that would have caught the `explore_filters.py` gap. Existing `test_filter_pool_excludes_saved`
    passes unmodified.
  - Mutation-tested: temporarily broke the `>=`/latest-wins logic, confirmed the new tests
    fail, restored, confirmed green again.
  - Full `pytest` suite green.
  - Manually verified against the running dev server (Streamlit-widget logic isn't
    unit-tested here, per this repo's own documented exemption): the confirm-step Cancel path
    truly cancels; the Clear-all path truly clears AND reopening "⋯" afterward shows the
    normal single button again, not a stuck "Clear all 0" prompt (the specific bug the
    ordering fix prevents, checked explicitly); removing a saved company makes it reappear in
    the Discover pool (the specific bug the `explore_filters.py` fix prevents, checked
    explicitly); 0-saved and 1-saved copy both read grammatically.
  - `docs/ui/saved_list.md`, `docs/north_star.md`,
    `docs/backlog/discover_saved_search_ux_findings.md` updated per the plan.
  - No em dash or en dash on any added line.

impact_map:
  - Behavior change, not just docs/tests this time: the Discover pool's saved-exclusion logic
    changes (previously permanent once saved, now correctly reversible), and the Saved tab
    gains a new button and a two-state popover flow. Every existing user's stored interactions
    contain zero `"unsave"` rows today, so behavior is unchanged until the first removal
    happens -- backward compatible, no migration needed.
  - `frontend/*` and `tests/*` both touched -- per `.claude/review_routing.json`, this requires
    cto-reviewer in addition to scope-auditor (`always`).
  - No new dependency, no schema/CI change, no new mechanism beyond the pure-function
    extraction pattern this repo already uses repeatedly (e.g. `_sync_search_query`).

amendments:

2026-09-05 -- scope-auditor's first pass FAILED on five findings; four addressed here, one
disclosed as deliberately not addressed:

1. Two added lines (`docs/ui/discover_header.md`, `docs/ui/saved_list.md`) contained a real
   em dash despite the intent being `--` -- fixed. A repo-wide sweep restricted to added diff
   lines only (not whole-file, which would false-positive on this repo's considerable
   pre-existing em-dash use) confirmed no others.
2. `docs/ui/discover_header.md` was edited but missing from `scope_paths` -- added above.
3. This contract referred to the shared helper as `_saved_keys_with_order` (leading
   underscore) throughout, a stale name from before it was made public -- corrected to
   `saved_keys_with_order` everywhere in this file, matching what was actually implemented.
4. `decisions_reserved`'s per-item-removal reasoning read as self-classified by analogy --
   corrected above to cite the actual plan-mode approval trail, which a cold reviewer has no
   way to see otherwise since the plan file lives outside this repo.

Not addressed, disclosed instead: `.claude/active_work.md` showed zero change while listed in
`scope_paths`. Fixed by actually updating it in this same commit (see below) rather than
deferring -- unlike `review.md`, it has no structural reason to wait.

A non-blocking note from the same review, tracked but not fixed here (out of this task's
scope, no live path affected): `supabase/migrations/001_initial_schema.sql`'s
`user_interactions.action` CHECK constraint still only allows `('save', 'skip')`, now stale
against the app-level `'unsave'` action. Nothing in this codebase currently writes to that
table (`browser_storage.py` only ever touches browser localStorage), so no live constraint
violation exists today -- flagged in `.claude/active_work.md`'s Open items for whoever builds
the deferred cross-device-sync feature that table is reserved for.
