# Task contract
> DISPOSABLE. **Owns:** THIS task's objective, `scope_paths`, reserved decisions and
> `done_when`.
> **Never:** anything that outlives the task. Overwritten by the next one.

objective: Raise the mobile type scale so body copy is 14px and nothing renders under 12px.

  Before the change the caption token (0.72rem, 11.5px) carried body copy at most
  `font-size` sites in `frontend/styles.py`, and the hardcoded sizes went down to 0.65rem.
  The live counts at 375px are in the MR description.

scope_paths:
  - frontend/styles.py
  - docs/ui/design_system.md
  - docs/ui/card_metric_cell.md
  - tests/frontend/test_styles.py
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/active_work.md

decisions_reserved:
  - The scale. Owner-set: body 14px (new `--ss-body`, 0.875rem); captions and meta lines 13px
    (`--ss-caption-size` from 0.72rem to 0.8125rem); chips and small uppercase labels 12px
    (`--ss-label`, unchanged, now the floor); list-row titles 15px (`--ss-row-title` from
    0.85rem to 0.9375rem); card title 17px (`--ss-title` from 1rem to 1.0625rem); the big
    metric value 24px unchanged. The brand wordmark (1.35rem) and the icon-button glyph
    (1.05rem) are not text sizes and are unchanged.
  - Which text is body and which is caption at each site is the agent's reading
    of what the text is; the owner saw the result live at 375px in the session.
  - The fold. Measured on a long financial card at 480x812: the first metric value sat 20px
    above the fold before and sits 64px below it after; at 375x812 it was below the fold
    before the change. Owner chose to ship the scale and take the ~300px of header above the
    card (brand, tagline, disclaimer, nav, saved count, back button) as the next UI piece,
    over holding this change until that layout is designed.

done_when:
  - Every `font-size` in `frontend/styles.py` uses a token; no hardcoded size remains below
    the wordmark and icon glyph.
  - A test in `tests/frontend/test_styles.py` asserts every `font-size` in the stylesheet is
    a token reference or one of those two named exceptions, and that no size token resolves
    under 0.75rem.
  - At 375px: no visible text element under 12px on Discover, the card or Saved; no
    horizontal scroll; Save reachable on Discover; company and verdict visible without
    scrolling. The first-metric-above-the-fold check is the reserved decision above.
  - `docs/ui/design_system.md` tokens table lists the type tokens with the new values;
    `docs/ui/card_metric_cell.md`'s typography line names the body token, not 0.78rem.
  - Before and after measurements at 375px and 480px in the MR; the repo has no browser
    driver to write screenshot files, and the owner reviewed the screens live.

impact_map: Frontend CSS only. Larger type lengthens every card; the 480px first-metric
  check is the guard against pushing it below the fold. No data, no export, no copy change.
