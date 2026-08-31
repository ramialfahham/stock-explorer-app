# Task contract

objective: Fix the Discover/Saved/Search row tap-target misalignment the owner reported (not
  all row areas clickable, clicking one row opens the row above it, the first row does nothing
  at all). Diagnosed by direct DOM measurement, not guesswork: every row's invisible
  full-row tap-target button was rendering entirely *below* its own visible row instead of on
  top of it, because Streamlit sets `position: relative` on the `stElementContainer` that
  directly wraps the button, and since that wrapper is nearer than the intended
  `stVerticalBlock` anchor, it becomes the button's containing block instead; the wrapper has
  no content of its own so it collapses to zero height, and the button renders at its
  `min-height` starting wherever that zero-height box falls in normal document flow, i.e. right
  after the row's own markdown. This is a pre-existing bug (confirmed via `git log` on
  `frontend/row_ui.py`/`frontend/styles.py`: the overlay mechanism predates this session's own
  changes, including the verdict-dot fix), affecting all three tabs equally since Saved, Search,
  and Discover all share the same row primitive.

scope_paths:
  - frontend/styles.py
  - tests/frontend/test_styles.py
  - .claude/task/contract.md
  - .claude/task/review.md

decisions_reserved: (none; this is a bug fix with an already-diagnosed, mechanically-verifiable
  root cause, not a product/UX decision)
  - **Found by round-1 cto-reviewer review: the regression guard's regex was too weak.** The
    first draft matched only the selector's tail (`[data-testid="stElementContainer"]:has(>
    [data-testid="stButton"]) { ... position: static !important`), never anchoring the
    `:has(.ss-row-group) div[data-testid="stVerticalBlock"]:has(.ss-row)` prefix that is the
    entire reason `!important` is safe to ship. Verified by the reviewer's own mutation probe:
    a hypothetical future edit that dropped the scoping prefix, turning the rule global
    (forcing `position: static` on every `st.button()`'s wrapper in the app, confirmed via grep
    that this selector shape is otherwise unique in the file), would still satisfy the regex.
    Fixed: extended the pattern to require the full selector chain, re-verified with the same
    mutation probe (correct form matches, all three broken variants, including the
    reviewer's newly-found one, no longer match).

done_when:
  - `frontend/styles.py` gains a rule resetting `position` on the `stElementContainer` that
    directly wraps a row's tap-target button (scoped to `:has(.ss-row-group)
    div[data-testid="stVerticalBlock"]:has(.ss-row)`, matching the existing scoping pattern),
    so the button's `position: absolute; inset: 0` skips that wrapper and correctly resolves
    against the row-level `stVerticalBlock` instead.
  - `tests/frontend/test_styles.py` gains a regression guard matching this file's own
    established pattern (a regex checking the fixed rule's shape is present in
    `frontend/styles.py`), verified to genuinely fail against the broken form (reverting the
    fix) and pass with it applied, not just plausible-looking.
  - Live verification, not assumed from the CSS: every sampled row's tap-target bounding box
    matches its own visible row's bounding box exactly (not the previous behavior, where it sat
    below and overlapped the next row); confirmed via real pixel hit-testing
    (`document.elementFromPoint`) at both the top and bottom edge of several rows, not just
    programmatic `.click()` calls on element references (which bypass hit-testing and would not
    have caught this bug); confirmed the correct company opens when a row is clicked, including
    specifically the first row (previously dead) and a row whose visible area previously
    overlapped with the row above it; confirmed the same fix applies to Saved's rows (shared
    primitive).
  - `pytest` green.
  - No em dash or en dash on any added line.

impact_map:
  - Every row in Discover, Saved, and Search is affected: this was the core click-to-open
    interaction for the entire app, broken since before this session's work (not a regression
    introduced by the verdict-dot fix or any other change made this session).
  - CSS-only change; no Python logic, no HTML structure change, no new dependency.
  - No dbt, ingestion, or data model change. Display/interaction only.

amendments: (none)
