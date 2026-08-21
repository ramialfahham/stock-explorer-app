# Task contract

objective: **Replace the card's two flat-scroll disclosure surfaces with per-item
  progressive disclosure**, reusing the existing `disclosure_html()` component rather than
  inventing a new one. Two surfaces: (1) the company description gets its own inline
  "Read more" toggle directly under the card-face preview, instead of living at the bottom
  of the "Understand these numbers" panel; (2) each metric's full explanation in "What each
  metric means" gets its own toggle instead of all metrics' full paragraphs rendering
  concatenated and always-visible. Raised live by the owner testing the deployed app,
  researched against NN/g's progressive-disclosure and accordion guidance, wireframed and
  approved in conversation before this contract was written.

scope_paths:
  - frontend/disclosure_html.py           # preview param becomes optional (skip empty <p>)
  - frontend/card_ui.py                   # both disclosure surfaces + _company_about_body_html() removed
  - frontend/styles.py                    # toggle underline (shared rule); drop dead .ss-metric-gloss-inline
  - dbt_analytics/seeds/metric_catalogue.csv  # ebit_margin_pct learn text (Option A, owner-picked)
  - frontend/metrics.json                 # regenerated output, not hand-edited
  - tests/frontend/test_card_ui.py        # tests for both new disclosure surfaces
  - tests/frontend/test_disclosure_html.py # round-1 review finding: cover the new falsy-skippable preview branch
  - docs/ui/disclosure_pattern.md         # flip "no longer uses this pattern" back; Backlog -> Shipped
  - docs/ui/card_metric_cell.md           # "Deep copy lives in Understand these numbers" no longer covers about-company
  - docs/north_star.md                    # Deep-tier row: about-company delivery mechanism changed
  - .claude/task/contract.md

decisions_reserved (owner-approved this session, in conversation):
  - **Reopening Slice 6c's "one disclosure per card" and "flatten 11 metric toggles into
    one list" decisions** — both explicitly reopened by the owner after seeing the live app;
    not the agent's call, owner-initiated.
  - **Toggle color**: keep the existing `--ss-accent` gold (consistent with the Saved-headline
    toggle already using it), add underline so it doesn't blend with `.ss-metric-analogy`
    (same gold, no underline) sitting right next to it on the per-metric surface — owner
    confirmed this reads clearly in the wireframe.
  - **`ebit_margin_pct` learn copy**: owner flagged "This card sums..." as bad opening
    phrasing (the one metric, of 16, that opens by referencing the UI instead of defining
    the metric). Owner picked "Option A" from two drafts offered, framed against the other
    15 metrics' established opening pattern (define the metric first). Round-1 review then
    caught a real accuracy gap in Option A as drafted — it dropped the word "divide,"
    describing the calculation as summing two numbers without stating the division that
    makes the result a margin. Round-2 review then caught the fix's own grammar: "summed
    across the last four quarters" read, by ordinary proximity parsing, as modifying only
    "Total Revenue" — leaving Operating Income's period unstated and inviting a beginner to
    compute roughly a quarter of the true margin. Both fixed without a second owner
    round-trip (factual/clarity completions, not new framing decisions) — final approved
    text, verbatim, matching the seed byte-for-byte:
    > Operating margin measures how much profit is left from each dollar of sales after
    > operating costs, before interest and taxes. This figure divides Operating Income by
    > Total Revenue, both summed across the last four quarters — a trailing twelve-month
    > (TTM) margin, not Yahoo's single-quarter snapshot.
  - **Redundant gloss line dropped** from the per-metric learn block (`.ss-metric-gloss-inline`,
    `ss-metric-gloss-inline` class + its one call site) — owner's own strikethrough
    annotation on a screenshot; it restated the label in flatter language once the full
    paragraph sits behind its own toggle.

technical_definition:
  - `disclosure_html()`: `preview` becomes falsy-skippable — when empty, the `<p
    class="ss-disclosure-preview">` is omitted entirely rather than rendered empty. Backward
    compatible: every existing caller (Saved headlines) passes real preview text, unaffected.
  - `_company_summary_html()` (`frontend/card_ui.py`): when `business_summary_is_truncated()`
    and a full text exists, returns `disclosure_html()` output (preview = the existing
    truncated preview, full body = the existing `.ss-company-summary-full` paragraph) instead
    of a plain `<p>`. Short/non-truncated descriptions unchanged (plain `<p
    class="ss-company-summary">`, no toggle — there's nothing more to reveal).
  - `_company_about_body_html()`: deleted. Nothing calls it once about-company isn't
    duplicated into the learn panel.
  - `build_learn_panel_body_html()`: drops the about-company section entirely (was already
    last per last session's fix; now absent). Compare section and "What each metric means"
    heading unchanged.
  - `_metric_learn_blocks()`: per metric, drops the `.ss-metric-gloss-inline` paragraph and
    wraps the existing `.ss-metric-learn-body` paragraph in `disclosure_html(preview="",
    full_body_html=..., more_label="Read more", less_label="Show less")` instead of
    rendering it unconditionally. `.ss-metric-learn-heading` and `.ss-metric-analogy` stay
    exactly as they render today, unconditionally visible.
  - `frontend/styles.py`: `.ss-disclosure-more, .ss-disclosure-less` gets `text-decoration:
    underline` (one shared rule — every `disclosure_html()` consumer gets it, not scoped to
    one surface, matching this repo's established no-per-surface-exception convention).
    `.ss-metric-gloss-inline` rule deleted (confirmed its one Python call site is also
    removed in the same diff — zero remaining consumers).
  - `dbt_analytics/seeds/metric_catalogue.csv`: `ebit_margin_pct` row's `learn` field
    replaced with Option A text. (A `�` seen while inspecting this field via a Bash/Python
    print earlier turned out to be a terminal print-encoding artifact, not a real bug in the
    file — confirmed via a direct Read of the raw CSV line, which shows a correctly encoded
    em dash. No encoding fix needed; noting this so the false lead doesn't get repeated.)
  - `frontend/metrics.json`: regenerated via `python scripts/export_metric_definitions_json.py`
    after the seed edit — never hand-edited, per the file's own header comment.
    `tests/tooling/test_metric_catalogue.py`'s existing no-drift lock (regenerates and
    diffs against the committed file) is what catches a forgotten regen.

explicitly_not_in_scope:
  - Any other metric's copy — only `ebit_margin_pct`'s opening sentence, the one confirmed
    outlier among 16.
  - Any further metric-cell visual-hierarchy work (magnitude cues, min-median-max range
    marks) discussed earlier in the same conversation — separate, still-unscoped follow-up.
  - Multi-open vs. single-open enforcement — native `<details>` are independent by default,
    so "several can stay open" (the NN/g-informed requirement) falls out for free; no new
    JS/state needed, nothing to explicitly build for it.

done_when:
  - Card face: truncated company descriptions render a real `disclosure_html()` toggle in
    place; short ones render exactly as before (no toggle).
  - `build_learn_panel_body_html()` never contains "About this company" — that section is
    gone from the learn panel entirely, not just reordered.
  - Each metric in "What each metric means" renders its own `<details>`; `.ss-metric-gloss-inline`
    does not appear anywhere in the output.
  - `frontend/metrics.json` regenerated and byte-identical to what
    `scripts/export_metric_definitions_json.py` produces from the edited seed (the existing
    no-drift test enforces this).
  - Full test suite green, including new/updated tests for both disclosure surfaces.
  - Verified against the real app (local Streamlit + live Supabase) via the Browser pane —
    both toggles clickable and independently open/closeable; 480px mobile smoke, zero
    horizontal scroll.
  - `docs/ui/disclosure_pattern.md`, `docs/ui/card_metric_cell.md`, `docs/north_star.md` all
    updated to match — none left describing the mechanism this diff replaces.
  - UX PR gate: mobile wireframe in the PR body (ASCII, derived from the approved interactive
    wireframe already shown in conversation); one-sentence primary-job statement.
  - Required reviewers (scope-auditor always; cto-reviewer per `frontend/*`/`tests/*`;
    equity-analyst-reviewer per `*metric_catalogue.csv`) pass against the staged diff.

impact_map:
  - User-facing: every card, all markets, all company types — company description and
    per-metric explanations both change interaction model. No metric values, verdicts, or
    benchmark comparisons change.
  - One metric's (`ebit_margin_pct`) explanatory copy changes; no other data or copy.
  - No pipeline/CI-variable/schedule impact — frontend + one dbt seed only.

amendments: none yet.
