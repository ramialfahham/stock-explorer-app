# Task contract

objective: Fix the Discover list's verdict dot alignment, per explicit owner decision after a
  live investigation: replace the native color emoji (🟢/🟡/🔴) with a plain CSS-drawn circle,
  same colors, same meaning, no word label. Measured directly in the running app: every row's
  own flexbox layout was already pixel-identical (bounding-box offset exactly 0.0 across every
  sampled row), so the "scattered" look was never a CSS positioning bug; it was the emoji
  glyph's own internal vertical metrics, which vary by platform/font and are outside anyone's
  control. A CSS-drawn dot is pixel-exact everywhere by construction. Explicitly does NOT add a
  text label next to the dot: the owner correctly flagged that a word (e.g. "Healthy") sitting
  next to the row's one displayed metric would read as if it rated that specific number, when
  the verdict is actually derived from 3-6 different metrics depending on company type. The
  dot's color and meaning are unchanged from the already owner-approved verdict mechanism
  (Slice 6c); this task is a rendering-technique fix, not a new design decision.

scope_paths:
  - frontend/row_ui.py
  - frontend/app.py
  - frontend/styles.py
  - tests/frontend/test_row_ui.py
  - docs/ui/discover_list.md
  - .claude/task/contract.md
  - .claude/task/review.md

decisions_reserved:
  - **None of the color/meaning/mechanism is reserved here**: the owner already decided (same
    colors, no word label, CSS dot instead of emoji) after a live investigation in
    conversation. What's reserved is exact color values for the CSS dot, which weren't given a
    specific hex by the owner (only "same colors" as a constraint): chose readable,
    dark-background-appropriate green/amber/red (`--ss-verdict-green: #3fb950`,
    `--ss-verdict-yellow: #f0b429`, `--ss-verdict-red: #ef5350`) approximating the native
    emoji's hue family rather than matching any single platform's exact rendering (no single
    "correct" emoji color exists across platforms in the first place). If these read as too
    bright/dark/saturated once live, that's a fast follow-up, not a blocker.
  - The full card's own verdict badge (`frontend/card_ui.py`, `.ss-verdict-emoji`) is untouched
    on purpose: it renders once per card, not repeated hundreds of times down a scrolling list,
    so it doesn't exhibit the row-to-row alignment problem this task fixes. Not scope creep to
    leave it alone; scope creep would be touching it without being asked.

done_when:
  - `frontend/row_ui.py`'s `build_rich_row_html` takes `verdict: tuple[str, str] | None`
    (`(token, label)`) instead of `verdict_emoji: str | None`, and renders an empty
    `<span class="ss-row-verdict ss-row-verdict--{token}" role="img" aria-label="{label}">`
    instead of an emoji character. `render_rich_row_list`'s `verdict_fn` type hint updated to
    match.
  - `frontend/app.py`'s `_discover_row_verdict` returns `(token, VERDICT_BADGE_LABEL[token])`
    instead of the emoji string; `VERDICT_EMOJI` import replaced with `VERDICT_BADGE_LABEL`
    (already existing, owner-approved vocabulary: Healthy/Mixed/Fragile, unused anywhere else
    in `app.py` before this).
  - `frontend/styles.py`: `.ss-row-rich .ss-row-verdict` is a fixed-size (`0.6rem`) circle
    (`border-radius: 50%`), colored via three new modifier classes reading three new `:root`
    tokens (`--ss-verdict-green/yellow/red`). No emoji-sized font rule remains.
  - `docs/ui/discover_list.md`'s wireframe and "Right" description describe a dot, not an
    emoji, and explain why (glyph metrics vary by platform, a CSS shape doesn't).
  - New test: `build_rich_row_html` never emits an emoji character for a verdict, only the
    color-modifier class and the `aria-label`. Existing verdict/metric tests updated to the new
    tuple parameter shape, not just made to pass mechanically.
  - `pytest` green.
  - Live verification (not assumed from the CSS): every sampled row's dot sits at the exact
    same vertical offset relative to its row (measured via `getBoundingClientRect()`, not
    eyeballed), confirming the alignment fix actually holds in the running app, not just in
    theory.
  - No em dash or en dash on any added line.

impact_map:
  - Every Discover list row's right-hand verdict indicator changes rendering technique (dot
    instead of emoji); same colors, same meaning, same position. Saved and Search are
    unaffected (they use the plain `build_row_html`, never `build_rich_row_html`).
  - No dbt, ingestion, or data model change. Display only.

amendments: (none)
