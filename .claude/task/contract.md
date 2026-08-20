# Task contract

objective: **Slice 6b — Landing/Overflow unification.** Second of three phases of the UI
  redesign (Slice 6). Slice 6a (merged, MR #4) built the token/component foundation and
  explicitly deferred one gap: `docs/ui/design_system.md`'s anti-patterns list says "Extending
  the primary/secondary button color skin to Overflow/Landing under this doc's authority —
  that's 6b." The owner's instruction for this slice was explicit: "100% consistent design
  language for the whole web app" — not narrowly just Landing/Overflow. Exploration (grepping
  every `st.button`/`st.popover`/`st.expander` call in `frontend/`) found two more genuine gaps
  of the same shape: the "Filters" popover trigger (`app.py:302`) has zero custom CSS (a
  different widget type, `stPopoverButton`, never touched by 6a's button-radius rule), and
  `st.expander` (Overflow's "About the data" + the card's "Practice with hypothetical numbers")
  renders with fully native, unstyled Streamlit chrome in both places. This slice closes all
  three gaps with one generic CSS rule per widget type (buttons, popover triggers, expanders),
  not one-off per-surface patches. Approved plan: ~/.claude/plans/pure-juggling-frost.md
  (Slice 6b section, above the archived 6a section in the same file).

scope_paths:
  - frontend/styles.py                              # button skin globalized; new popover-trigger + expander rules
  - docs/ui/design_system.md                         # button-variants section updated; new popover/expander bullets
  - docs/north_star.md                               # only if a doc-sync gap is found during implementation
  - docs/working_agreement.md                        # only if a doc-sync gap is found during implementation
  - .claude/task/contract.md

decisions_reserved (owner-approved this session):
  - **"100% consistent design language for the whole web app"** — the owner's explicit
    correction after I initially proposed a narrower "just the four Landing/Overflow buttons"
    scope. This licenses generalizing the button-color skin app-wide (not just Landing/
    Overflow) and sweeping in the two other same-shape gaps found (Filters trigger, both
    `st.expander` instances) rather than leaving them freshly inconsistent.
  - **Correction, not a decision:** I initially asked whether to normalize Landing's serif
    "Fraunces" hero title (thinking it a one-off inconsistency). Investigation showed this was
    based on incomplete information — the exact same Fraunces family is already the app's
    brand typeface, used identically at the persistent `.ss-brand` header (styles.py:80,
    1.35rem) shown on every other page. A bigger hero treatment of the same brand mark is
    normal scaling, not an inconsistency. **No change to Landing's typography in this slice** —
    this was withdrawn as a question, not decided either way by the owner.

technical_definition:
  - **Button color skin globalized:** `frontend/styles.py`'s existing
    `.ss-action-shell + div[data-testid="stHorizontalBlock"] button[kind="primary"/"secondary"]`
    rules (accent-gold primary, bordered-surface secondary — values from 6a, unchanged) lose
    the `.ss-action-shell + div[...]` prefix and become plain `button[kind="primary"]` /
    `button[kind="secondary"]`. No new colors — purely widening the selector.
  - **Full inventory of buttons this affects** (every `st.button(` call in `frontend/`,
    confirmed via grep): Discover's Save/Skip bar (already had this skin — true no-op there,
    the zero-diff check in `done_when`), Discover's end-of-scope "Start over in this scope"
    (primary) + "Next company" (secondary) (`app.py:345,364`), Saved's "← Back to list"
    (`app.py:389`), Landing's "Start exploring" (`landing.py:34`), Overflow's "How Stock
    Explorer works" / "Start over" / "Clear saved" (`overflow_menu.py:125,134,137`), Saved-news'
    "Try again" (`saved_news.py:191`). The row-overlay tap buttons (`row_ui.py`) are unaffected
    — their own more-specific `!important` rule (styles.py ~538-548) already wins regardless of
    what a broader rule sets; verified, not assumed, per `done_when`.
  - **New popover-trigger rule:** `[data-testid="stPopoverButton"] { background:
    var(--ss-surface) !important; border: 1px solid var(--ss-border) !important;
    border-radius: var(--ss-radius-control) !important; }` — covers the previously-unstyled
    "Filters" trigger. Does not conflict with the existing icon-button-marker rule for the "⋯"
    trigger (styles.py ~752), which redeclares the same three properties plus its own square
    sizing — same harmless redundant-match pattern the cto-reviewer explicitly approved for
    6a's row-primitive rules.
  - **New expander rule:** one global `[data-testid="stExpander"]` rule (bordered,
    `var(--ss-surface)` fill, `var(--ss-radius-surface)` corners — the surface tier, same as
    the card and rows) covering both live instances (`overflow_menu.py`'s "About the data",
    `card_ui.py`'s "Practice with hypothetical numbers"). Exact internal selector confirmed
    against the live rendered DOM during implementation, not assumed from memory.
  - **Docs:** `design_system.md`'s "Button variants" section — remove the stale "Landing and
    Overflow-menu button reskinning beyond radius is 6b's job, not this doc's" line (6b
    resolves it) and state buttons are genuinely global now; add short "Popover trigger" and
    "Expander" bullets alongside the existing row/button primitives (this doc's own scope
    statement already covers "shared row/button primitives — the system underneath every other
    spec"). No new standalone Landing/Overflow content doc — this slice doesn't change what
    Landing/Overflow say or how they're laid out, only how their existing native widgets are
    skinned; `discover_header.md` already owns Overflow's content-order spec.

explicitly_not_in_scope:
  - Landing/Overflow's copy, layout, or content structure.
  - The Discover/Saved/Search segmented control — `design_system.md` already documents it as
    deliberately outside the button-variant system (native widget, own theming).
  - Any new design tokens — every value used here already exists from 6a (`--ss-accent`,
    `--ss-surface`, `--ss-border`, `--ss-radius-control`, `--ss-radius-surface`).
  - Landing's typography (see decisions_reserved — this was a withdrawn question, not a change).

done_when:
  - Discover's Save/Skip bar renders pixel-identical before/after globalizing its button rule
    (true no-op there — same values, wider selector).
  - Landing's "Start exploring", Overflow's three buttons, Discover's two end-of-scope buttons,
    Saved's "← Back to list", and Saved-news' "Try again" all render with the same accent/
    surface skin as the Discover action bar.
  - "Filters" popover trigger and the "⋯" overflow trigger render with the same surface/border/
    radius look; the "⋯" trigger's own square sizing is unaffected.
  - Both `st.expander` instances (Overflow "About the data", card "Practice with hypothetical
    numbers") render bordered/filled instead of native Streamlit grey chrome.
  - Row-overlay tap buttons (Saved list, Search results) remain fully invisible — no border/
    background leaking through from the new global button rule.
  - `pytest tests/` stays green (pure CSS + doc change, no Python logic touched).
  - Real screenshots (Browser pane or the CDP-harness fallback from 6a) of Landing, the open
    Overflow popover, the open Filters popover, and both expanders — before and after.
  - scope-auditor (always) + cto-reviewer (`frontend/*`) both PASS on the final staged diff,
    per `.claude/review_routing.json`.

impact_map:
  - Pure frontend CSS + one doc update. No backend/data/migration change, no new dependency.
    Required reviewers (per `.claude/review_routing.json`): **scope-auditor** (always) ·
    **cto-reviewer** (`frontend/*`). Neither analytics-engineer nor data-engineer nor
    equity-analyst-reviewer route to this diff.
  - Also subject to the project's **UX PR gate** (`docs/working_agreement.md`) — a separate,
    project-specific requirement for any Streamlit layout/copy/interaction change (this is a
    visual-skin change, not layout/copy, but the gate's 480px-smoke habit still applies).

amendments:
  - **scope-auditor FAIL (round 1), fixed — three findings:**
    1. **`st.link_button` gap (the substantial one).** The original diff's button inventory
       greped only `st.button(` calls, missing `st.link_button` entirely — the card footer's
       "Yahoo Finance" link (`card_ui.py:233`, rendered on every card: Discover, Saved focus,
       Search focus) rendered as an `<a>`, not a `<button kind="...">`, so it was structurally
       invisible to the new global rules and stayed unstyled while everything else got
       unified. This directly undercut the "100%, whole app" authority the contract cites.
       **Fixed, and a second, deeper bug found while fixing it:** live DOM inspection showed
       the real rendered attribute is `data-testid="stBaseLinkButton-secondary"`, not
       `"stLinkButton"` as both my new rule AND a **pre-existing** (pre-6b) footer-scoped
       sizing rule (`styles.py`, `.ss-card-footer-shell + ... a[data-testid="stLinkButton"]`)
       assumed — meaning that older rule's font-size/min-height/padding/text-decoration have
       never actually applied to this element, since before 6b started. Fixed both: added a
       new global `a[data-testid="stBaseLinkButton-secondary"]` rule (same surface/border/
       control-radius skin as a secondary button) and corrected the pre-existing rule's
       selector to the real testid. Verified live: computed styles now show
       `background: rgb(20,20,22)` / `border: 1px solid rgb(39,39,42)` / `border-radius: 8px`
       — matching `--ss-surface`/`--ss-border`/`--ss-radius-control` exactly.
    2. **Stale comment**, fixed. `styles.py`'s original 6a comment above the button-radius
       rule ("Colors/backgrounds are NOT set here... until 6b unifies Landing/Overflow") went
       unedited by this diff while a second comment two sections below said the opposite —
       two comments in the same file disagreeing about current state. Updated the first to
       reflect that 6b did close that gap.
    3. **Segmented-control leak risk, verified rather than re-asserted.** The contract claimed
       the nav pills stay unaffected by the widened `button[kind=...]` selectors but never
       proved it the way it proved the row-overlay-button claim (CSS specificity math). Now
       verified live: the segmented control's pill elements carry `kind="segmented_control"`/
       `"segmented_controlActive"` (confirmed via `[data-testid^="stBaseButton-segmented_control"]`
       in the live DOM), distinct string values from `"primary"`/`"secondary"` — attribute
       selectors are exact-match, so there is no leak. The cto-reviewer independently confirmed
       this same fact from the pinned `streamlit==1.57.0` bundle's own kind enum.
  - **Round 2 — mechanical bug in this file, fixed:** a duplicate top-level `amendments:` key
    (a stray `amendments: (none yet)` leftover from the original template, never removed when
    the round-1 amendment above was appended). Removed. Flagged independently by both
    reviewers, who also each escalated the same underlying question rather than failing or
    passing outright:
  - **cto-reviewer ESCALATE + scope-auditor FAIL (round 2) — same question, now owner-decided:**
    was it appropriate to fold the pre-existing (out-of-slice) footer-link-rule testid bug fix
    into this diff, discovered incidentally while fixing the in-scope `st.link_button` gap?
    **Owner decision: keep it bundled** (same file, same CSS rule, same root cause — a rule
    already known dead within this very diff would otherwise ship uncorrected right beside the
    freshly-fixed live one referencing the same DOM node).
  - **cto-reviewer ESCALATE, owner-decided:** should the new link-button skin also cover the
    `-primary`/`-tertiary` `stBaseLinkButton` variants, which have zero live consumers today
    (the one call site, `card_ui.py:233`, uses the default `secondary`)? **Owner decision:
    cover all three now**, so a future `st.link_button(type="primary")` never silently ships
    unstyled the same way this round's bug did. `-primary` reuses the accent skin from
    `button[kind="primary"]`; `-tertiary` shares `-secondary`'s surface skin rather than
    inventing a third color tier this app has no precedent for anywhere else.
