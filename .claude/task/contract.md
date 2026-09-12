# Task contract
> DISPOSABLE. **Owns:** THIS task's objective, `scope_paths`, reserved decisions and
> `done_when`.
> **Never:** anything that outlives the task. Overwritten by the next one.

objective: Put the first metric value back above the fold on a phone when a card is open.

  Measured at 375x812 on a typical card after the type scale: the card starts at 270px (brand
  66, nav 38, saved-count line 29, back button ~50, plus gaps) and the first metric value sits
  at 978px, with the AI-written paragraph taking 284px and "About the company" 114px of the
  card itself. A zero-height header alone would leave the first metric at ~708px on this card
  and below the fold on longer ones, so the header is a third of the problem.

scope_paths:
  - frontend/app.py
  - frontend/card_ui.py
  - frontend/card_copy.py
  - frontend/styles.py
  - tests/frontend/test_app.py
  - tests/frontend/test_card_ui.py
  - tests/frontend/test_app_e2e.py
  - docs/ui/discover_header.md
  - docs/ui/disclosure_pattern.md
  - docs/north_star.md
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/active_work.md

decisions_reserved:
  - Composition, owner-set, both levers: (1) while a card is open, the header drops the tagline
    and the "Not investment advice" line (both stay on every list view, which every visit
    starts from) and the back button shares one row with the saved count; (2) the AI-written
    paragraph opens folded to its first lines with the card's existing Read more / Show less
    toggle; the verdict badge, the block label and the financial caveat stay fully visible.
  - The fold length in words is the agent's: enough for about three lines at 375px and 14px.

done_when:
  - `_health_block_html` renders the AI read through `disclosure_html` when it exceeds the
    preview length, with the full text inside the toggle and the caveat outside it; a short
    read renders plain, as the company summary already does.
  - On a focused card (Discover and Saved), the header renders the brand only, and the back
    button and saved count share one row; list views are unchanged.
  - Tests in `tests/frontend` pin: the fold and its labels; a short read not folded; the
    caveat outside the toggle; the badge and label outside the toggle; the compact header's
    content; `_card_open` following the Discover and Saved focus keys and never Search; and,
    through AppTest driving the real script, the header compact with a card open, full again
    on Back and on a tab switch, with the stats line gone while the back row shows the count.
  - Measured at 375x812 on the card that measured 978px before: the first metric value above
    the fold; at 480x812 on the long financial card that measured 876px: above the fold.
  - `docs/ui/discover_header.md` rows 2, 3 and 6 state the focused-view behaviour;
    `docs/ui/disclosure_pattern.md` lists the AI read as a placement; `docs/north_star.md`'s
    mobile success check names what makes it hold instead of saying it was not re-verified.

impact_map: Frontend only. Two card-face behaviours change: the header while a card is open,
  and the AI read's default state. The full read stays in the HTML, one tap away.
