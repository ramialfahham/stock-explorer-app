# Task contract
> DISPOSABLE. **Owns:** THIS task's objective, `scope_paths`, reserved decisions and
> `done_when`.
> **Never:** anything that outlives the task. Overwritten by the next task.

objective: Owner report (screenshot review): non-"Discover" interactive elements (list
  rows, Filters, search box) read as too visually similar to the near-black page
  background -- only the gold "Discover" active-nav pill stands out. Owner explicitly
  chose to stay within the existing monochrome constraint (`docs/ui/design_system.md`'s
  Authority line, from `north_star.md`) rather than introduce a new accent color.

  Iterated live (mockups, then a real dev-server trial) to reach a concept, not a one-off
  color pick, after the owner rejected two earlier ad hoc passes as inconsistent ("sometimes
  with a border, sometimes without... no concept"). Landed concept: two tonal tiers split by
  FUNCTION, not by screen -- **content tier** (rows, the card, `st.expander`, chips: read or
  tapped to navigate, no button chrome of their own, unchanged fill/border) vs **control
  tier** (every actual button/input a user operates: `button[kind="secondary"]`, its
  link-button twin, `st.popover` triggers incl. the icon variant, `st.text_input`: one step
  lighter fill + a visibly brighter border). Applied via the existing shared selectors, so
  it reaches every control app-wide in one rule, not just the ones on the Discover screen --
  this is what fixed the `Saved` nav pill and the `⋯` overflow trigger without touching them
  directly; the owner flagged both as still buried mid-review, before this app-wide framing
  was applied. Gold (`button[kind="primary"]`) stays reserved for the one primary action per
  view, untouched.

  Live-verified at mobile width (375px) against the real dev server, not synthetic swatches:
  Discover's search box, Filters, the nav row's `Saved` pill and `⋯` overflow trigger, and a
  card's `Not now` secondary action all read as one consistent "control" tier, visibly
  lighter than rows/the card, without any of them reading as loud as the gold pill. Owner
  confirmed: "looks better, write it up and open the MR."

scope_paths:
  - frontend/styles.py
  - docs/ui/design_system.md
  - docs/context_budget.yml
  - .claude/task/contract.md
  - .claude/task/review.md

decisions_reserved: Product/UX contrast direction was escalated and answered across this
  task's own back-and-forth -- monochrome vs new accent (owner: stay monochrome), and the
  final concept + values (owner: confirmed live against the real dev server, not a mockup).
  No decision left open.

done_when:
  - `--ss-surface-control`/`--ss-border-control` tokens exist in `frontend/styles.py`'s
    `:root` block, documented with a WHY comment distinguishing content vs control tier.
  - Every control-tier selector (`button[kind="secondary"]`,
    `a[data-testid="stBaseLinkButton-secondary"]`/`-tertiary`, `[data-testid="stPopoverButton"]`
    incl. the icon-button variant, `[data-testid="stTextInput"] input`) uses the new tokens;
    every content-tier selector (`.ss-row`, `stExpander`) is unchanged from before this task.
  - `docs/ui/design_system.md` documents the two new tokens in its existing Tokens table,
    with the content-vs-control rationale folded into the existing "Two radius tiers..."
    paragraph immediately below that table (not a new heading -- kept inline to stay inside
    this file's byte budget; the token table plus that paragraph is where a reader already
    looks for tier rules, per the radius precedent right above it), an anti-pattern bullet
    against dressing a content-tier element in control-tier chrome or vice versa, and an
    extended 480px smoke line for the visible content/control contrast.
  - `pytest tests/frontend/` passes (335 tests -- no color-token assertions existed to
    break, this is a pure visual/CSS change).
  - `check_no_em_dash.py` passes on the changed files.
  - `check_context_budget.py` passes -- `docs/ui/design_system.md` grew past its original
    10000-byte cap; `docs/context_budget.yml`'s own header sanctions raising the number in
    the same MR with a stated reason, done here (bumped to 10700, file sits at ~10620).
  - Live-verified against the real Streamlit dev server, mobile width -- done, owner
    confirmed directly in this session, not merely via a static mockup.

impact_map: `frontend/styles.py` (two new color tokens, five existing selector blocks
  repointed at them: `button[kind="secondary"]`, the combined link-button secondary/tertiary
  rule, `stPopoverButton`, its icon-button variant, and `stTextInput`; no new selector
  added), `docs/ui/design_system.md` (two new token rows + one extended paragraph + one
  anti-pattern bullet + one extended checklist line, no new heading), `docs/context_budget.yml`
  (one budget line raised, with the reason recorded here and in the MR description). No new
  component, no new Streamlit widget, no layout change -- pure recolor of existing chrome,
  so no mobile wireframe needed per the UX PR gate (`docs/working_agreement.md`), just the
  480px smoke already run live.
