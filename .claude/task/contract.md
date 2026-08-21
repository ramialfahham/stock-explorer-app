# Task contract

objective: **Fix content ordering in the card's "Understand these numbers" learn panel** —
  the panel opened with the full company description before any numbers content, so a
  control named for explaining metrics led with unrelated prose. Raised live by the owner
  testing the deployed app (not a pre-existing handover item); scoped to the minimal
  reorder, not the broader metric-cell visual-hierarchy redesign discussed in the same
  conversation (that's separate, unscoped work, deliberately deferred — see
  explicitly_not_in_scope).

scope_paths:
  - frontend/card_ui.py                 # build_learn_panel_body_html() reorder
  - tests/frontend/test_card_ui.py      # new regression test for section order
  - docs/ui/disclosure_pattern.md       # doc-sync: panel renders about-company last, and why
  - .claude/task/contract.md

decisions_reserved: none — pure reorder of existing, already-shipped sections; no new
  copy, no new mechanism, no styling change. Owner directed the fix ("Do #1 first") after
  reviewing the diagnosis in conversation (root cause traced to `docs/ui/disclosure_pattern.md`
  before any edit was made).

technical_definition:
  - `build_learn_panel_body_html()` in `frontend/card_ui.py`: `about_section` (the "About
    this company" block, from `_company_about_body_html()`) moved from first to last in
    the returned string concatenation. New order: benchmark-compare section →
    metric-definitions section → about-company section. Docstring updated to state the
    order is deliberate and why.
  - No change to `_company_about_body_html()`, `_benchmark_compare_body()`, or any other
    section-builder function — only the order they're assembled in.
  - New test `test_learn_panel_body_orders_numbers_content_before_company_description`
    asserts, via string-index comparison on the rendered HTML, that both the compare
    section and the metric-definitions heading appear before "About this company". None
    of the existing tests asserted order at all — how the original bug shipped unnoticed.
  - `docs/ui/disclosure_pattern.md` gets one clarifying paragraph: about-company renders
    last within the panel, and why — so a future addition to this panel doesn't
    reintroduce the same ordering mistake.

explicitly_not_in_scope:
  - The metric-cell visual-hierarchy redesign (flat/hard-to-scan stat display, monochrome
    constraint, no magnitude cue) — real design work requiring the owner's sign-off on a
    visual approach and, per the UX PR gate, a mobile wireframe if it changes card
    structure. Discussed in conversation as a second, separate piece of work; not started.
  - Any change to what the about-company section says, or to any heading text/copy —
    order only.

done_when:
  - `build_learn_panel_body_html()` returns compare → metric-definitions → about-company.
  - New regression test passes; full suite green.
  - Verified against the real app (local Streamlit + live Supabase, same card the owner
    screenshotted — Agilent Technologies) via the Browser pane: real rendered order
    confirmed compare → metric-definitions → about-company.
  - 480px smoke (mobile viewport, 375×812 preset): measured `document.documentElement`
    `scrollWidth`/`clientWidth` directly via javascript_tool on both the landing screen
    and the Discover card view after this fix — `375 == 375`, `hasHScroll: false` on
    both. No horizontal scroll introduced.
  - Required reviewers (scope-auditor, cto-reviewer per `frontend/*` routing in
    `review_routing.json`) pass against the staged diff.

impact_map:
  - User-facing: every card's "Understand these numbers" panel, all markets, all company
    types — pure content reorder, same information, nothing removed or added.
  - No data/pipeline/CI impact — frontend-only.

amendments:
  - **Review round 1: scope-auditor ESCALATE, cto-reviewer FAIL — both resolved.**
    - scope-auditor asked whether `docs/working_agreement.md`'s UX PR gate (north_star
      check, component-specs check, 480px smoke) applies in full to a pure content
      reorder within an unchanged expander, since the contract only addressed the
      mobile-wireframe bullet. Resolved with evidence, not judgment:
      `docs/north_star.md:80`'s Deep-tier row already specifies this exact order
      (compare → metric definitions → about-company → playgrounds) — confirmed by
      reading the doc directly. This diff isn't a new UX/content decision; it corrects
      Slice 6c's implementation drift from an already-approved spec. north_star.md is
      the component-specs authority for 4 of the 5 `docs/ui/*.md` files (verified via
      `grep -l north_star docs/ui/*.md`: `card_metric_cell.md`, `design_system.md`,
      `discover_header.md`, `saved_list.md` cite it; `disclosure_pattern.md` — the file
      this diff itself edits — does not cite it explicitly, though its content is a
      direct implementation of north_star.md's Deep tier regardless). Correcting an
      earlier, unverified overclaim in this same amendment ("cited by every
      docs/ui/*.md file") — round-2 scope-auditor caught it; fixed to the precise count
      above rather than restated loosely.
    - cto-reviewer found `render_learn_panel()`'s docstring (`frontend/card_ui.py`, the
      actual Streamlit entry point, ~17 lines below `build_learn_panel_body_html()`)
      still stated the pre-fix order — only one of the two docstrings describing this
      order had been updated. Fixed: now states the corrected order and cites
      north_star.md's Deep tier as the authority, matching the sibling docstring.
    - cto-reviewer additionally verified (empirically, not by inspection) that the new
      regression test genuinely fails against the reconstructed pre-fix code
      (`about_index < compare_index` under the old order) and passes under the new —
      confirmed a real regression test, not a tautology.
