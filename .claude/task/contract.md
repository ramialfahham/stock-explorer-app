# Task contract
> DISPOSABLE. **Owns:** THIS task's objective, `scope_paths`, reserved decisions and
> `done_when`.
> **Never:** anything that outlives the task. Overwritten by the next task.

objective: Two card-face/UX fixes flagged by the owner from a live screenshot. (1) The
  "What the numbers say - AI-written" block reads as one wall of text and hides most of it
  behind a Read more/Show less fold; render it as an always-visible bullet list instead, one
  sentence per bullet, nothing folded. (2) The "N saved" count currently renders on every
  tab's list header (Discover, Saved, Search) and again on the back-row when a card is open
  on Discover/Saved -- owner decided (2026-09-14) it should show on the Saved tab only.
  Addendum, same session: removing the fold left `docs/north_star.md`'s "first metric value
  above the fold" mobile success check contradicted by the now-always-full read -- owner
  decided (2026-09-14) to retire that check rather than re-guard it; swept every doc/comment
  that cited it.

scope_paths:
  - frontend/card_copy.py
  - frontend/card_ui.py
  - frontend/app.py
  - frontend/styles.py
  - tests/frontend/test_card_ui.py
  - tests/frontend/test_card_copy.py
  - tests/frontend/test_app_e2e.py
  - tests/frontend/test_styles.py
  - docs/north_star.md
  - docs/ui/disclosure_pattern.md
  - docs/ui/discover_header.md
  - docs/working_agreement.md
  - docs/product_roadmap_2026-06.md
  - tests/frontend/test_app.py
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/active_work.md

decisions_reserved:
  - "N saved" placement: owner chose Saved-tab-only (2026-09-14), over keeping it on
    Discover+Saved or de-duplicating it to once-per-screen on all three tabs.
  - "First metric value above the fold" mobile success check: owner retired it (2026-09-14)
    rather than re-guard it against the now-unfolded AI read.

done_when:
  - `_health_block_html` renders the AI-written read and the deterministic fallback through
    the same `_bullets_html()` code path -- `<ul>` of `<li>` sentences, fully visible, two
    classes (`ss-ai-read-list` / `ss-verdict-fallback-list`) so the two stay distinguishable
    in the DOM; no `<details>`/Read more/Show less anywhere in the health block.
  - A multi-sentence `ai_read` produces one `<li>` per sentence and the full text -- including
    its last sentence -- is present in the rendered HTML with no truncating "..." (mutation
    check: a test asserts the block contains zero "..." characters regardless of read length).
  - `ai_read_preview` / `AI_READ_PREVIEW_WORDS` removed from card_copy.py (dead once the fold
    is gone); `truncate_words` stays (business_summary_preview still uses it).
  - "N saved" appears only inside the Saved tab (its list header and its card-open back row);
    Discover's list header keeps "N match your filters" with no saved-count suffix; Discover's
    back row and the Search tab render no saved-count text anywhere (mutation check: a test
    renders each of the three tabs and asserts "saved" appears in the Saved tab's output and
    not in Discover's or Search's).
  - `pytest tests/ -q` green.
  - No remaining reference to "first metric value above the fold" (or the equivalent claim)
    as an active, tracked check anywhere in the repo (docs or code comments) -- grep confirms.

impact_map: Presentation-only in the Streamlit frontend -- no data contract, pipeline, or
  Supabase schema change. No new dependency, no cost.
