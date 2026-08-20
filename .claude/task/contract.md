# Task contract

objective: **Slice 6c — render new card content.** Third and final phase of the UI redesign
  (Slice 6). 6a (merged, MR #4) built the token/component foundation; 6b (merged, MR #9)
  unified button/popover/expander skin app-wide. 6c is the first slice that actually surfaces
  Slice 5's AI-assessment backend work (5a's deterministic 🟢/🟡/🔴 health verdict, 5b's Claude
  Haiku prose read) in the UI — `card_assessments` has never been fetched by `frontend/` at
  all until now. Owner confirmed this should be the full "approved mock" vision, not a
  minimal bolt-on: consolidate the card's ~11 separate disclosure toggles (company
  description, the "Understand these numbers" panel, a nested `<details>` per metric inside
  it, and the separately-expander'd "Practice with hypothetical numbers" playgrounds) into
  one; restyle metric labels as chips; replace the sector-benchmark arrow symbols (↑/↓/→)
  with the words already sitting in their tooltips. Approved plan:
  ~/.claude/plans/pure-juggling-frost.md (Slice 6c section, top of the file).

scope_paths:
  - frontend/supabase_cards.py     # new fetch_all_assessment_rows/fetch_card_assessments/fetch_eligible_cards_with_assessments
  - frontend/explore_filters.py    # new attach_assessments pure transform
  - frontend/app.py                # swap import, bump CARDS_CACHE_VERSION
  - frontend/card_copy.py          # VERDICT_EMOJI/VERDICT_BADGE_LABEL/VERDICT_MEANING/health_verdict_token/ai_read
  - frontend/card_ui.py            # health block, one-expander consolidation, words-not-arrows
  - frontend/metric_school.py      # only if render_metric_playgrounds's call signature needs to change
  - frontend/styles.py             # chip/badge CSS, dead-CSS removal
  - docs/ui/disclosure_pattern.md
  - docs/ui/card_metric_cell.md
  - docs/ui/design_system.md
  - docs/north_star.md
  - tests/frontend/test_card_ui.py
  - tests/frontend/test_explore_filters.py
  - tests/frontend/test_supabase_cards.py
  - .claude/task/contract.md

decisions_reserved (owner-approved this session):
  - **Full "approved mock" vision** (not a minimal bolt-on) — consolidate disclosures to one,
    label chips, words-not-arrows. All three explicitly confirmed, not assumed.
  - **AI read always visible**, right near the verdict badge — no click needed.
  - **Verdict badge label: emoji + one short word** — "Sturdy" (green) / "Mixed" (yellow) /
    "Strained" (red). Explicitly NOT the full `VERDICT_MEANING` sentence (redundant with the
    AI read directly below, which already ends on that same meaning) and NOT emoji-only.
  - **Words-not-arrows included in this slice's scope**, not deferred — the benchmark
    indicator's existing `_BENCHMARK_INDICATOR_LABELS` text ("Higher than sector median" /
    "Lower than sector median" / "At sector median") is already owner-approved copy (already
    shipped as a tooltip); this only changes whether it's shown visibly, not what it says.
  - **Correction, not a decision:** exploration found `docs/ui/card_metric_cell.md` already
    states "No hero/balance split; no side-by-side rows at any breakpoint" and
    `_metric_cell_html` renders every metric through identical markup today — there is no
    existing hero/secondary split for chips to selectively apply to. Chips apply uniformly to
    every metric; `north_star.md`'s older "hero three" framing (lines 46-52) is stale
    relative to the actual shipped code and is not being re-introduced by this slice.

technical_definition:
  - **Data plumbing:** `frontend/supabase_cards.py` gets three new functions
    (`fetch_all_assessment_rows`, `fetch_card_assessments`, `fetch_eligible_cards_with_assessments`)
    alongside the existing `fetch_all_eligible_rows`/`fetch_eligible_cards`, which are left
    untouched (their own test in `tests/frontend/test_supabase_cards.py` would break if the
    fixture's assumed table shape changed). `frontend/explore_filters.py` gets a new pure
    `attach_assessments(cards, assessments)` transform (same home as the existing
    `dedupe_to_latest_snapshot`). A card with no matching `card_assessments` row (the
    assessments pipeline runs after export and can lag a newly-eligible card) is returned
    unchanged — the health block is omitted entirely for that card, never a placeholder,
    matching this repo's established never-show-an-unvalued-dash convention. `ai_read` is
    nullable even when a row exists (per-card LLM failures are isolated in 5b) — badge shows,
    AI-read paragraph is omitted, when null.
  - **Copy:** `frontend/` (Streamlit Cloud) and `scripts/` (weekly pipeline) are separate
    deploy targets with no shared package today (confirmed via grep — nothing in `frontend/`
    imports from `scripts/`). `VERDICT_EMOJI`/`VERDICT_BADGE_LABEL` live in
    `frontend/card_copy.py`, owned there directly (not duplicated from `scripts/`). The plan's
    proposed `VERDICT_MEANING` duplication + sync-guard test was dropped mid-review (see
    `amendments`) — nothing in this slice's UI renders that sentence, so it shipped with zero
    consumers; re-add it, with its guard test, exactly when something needs it.
  - **One-expander consolidation:** confirmed technically sound before implementation —
    `render_metric_playgrounds` (real `st.number_input` widgets) already runs inside
    `with st.expander(...)` today; Streamlit's delta-path container model attaches widgets to
    whichever `with` block is active regardless of call depth, so mixing `st.markdown(html)`
    and live widgets in one expander is the same mechanism already in production, not a new
    risk. `render_learn_panel()` (new) replaces both the old HTML `<details class=
    "ss-learn-panel">` and the separate "Practice with hypothetical numbers" `st.expander` —
    one `st.expander("Understand these numbers")` containing: about-this-company (full
    description text, folded in per `north_star.md`'s own Deep-tier grouping — today's
    separate toggle is drift from that spec, not the spec itself), benchmark-compare-with-
    words, flattened per-metric definitions (no more nested `<details>` — a second click-deep
    toggle contradicts "one disclosure"), then the practice-number widgets in the same block.
    `render_stock_card`'s `show_metric_school` param renamed to `show_learn_panel`
    (grep-confirmed safe: never passed explicitly at any of its 3 call sites, only the
    default is used).
  - **Health block placement:** Scan tier — in `build_card_html`'s identity section, right
    after the name/ticker line, before the company description. First signal read after
    identity, per the owner-confirmed "always visible, near the verdict" AI-read decision.
  - **CSS:** every new value traces to an existing token (`--ss-bg`/`--ss-border`/
    `--ss-radius-control`/`--ss-space-1`/`--ss-space-2`/`--ss-label`/`--ss-muted`/`--ss-text`)
    — no new token invented. Dead-CSS removal (same precedent as 6a):
    `.ss-learn-panel`/`summary`/`::before` rules, `.ss-learn-panel-body`'s surface/border/
    radius (redundant with 6b's `[data-testid="stExpander"]` skin), `.ss-metric-learn-item
    summary`'s `<details>`-specific rules. `.ss-disclosure-*`/`disclosure_html()` itself is
    kept — still used by `saved_news.py`.

explicitly_not_in_scope:
  - A hero/secondary metric split — doesn't exist in the current code, chips apply uniformly
    (see decisions_reserved correction above).
  - Anything in Landing/Overflow (6b's territory, shipped) or the token system itself (6a's).
  - Shortening `_BENCHMARK_INDICATOR_LABELS`' existing text — only swap *where* it's shown,
    not *what* it says, unless a visual check shows it doesn't fit and the owner is asked
    separately (not decided in this contract).

done_when:
  - A card with a full `card_assessments` row shows the verdict badge (emoji + short word)
    and the AI read, both always visible, right after identity.
  - A card with no matching `card_assessments` row shows neither — no placeholder, no
    layout gap.
  - A card whose row has `ai_read = null` shows the badge but omits the AI-read paragraph.
  - The card's learn content (about-this-company, benchmarks, metric definitions, practice-
    number widgets) all live inside exactly one `st.expander("Understand these numbers")` —
    zero nested `<details>` remain in `build_card_html`'s output.
  - Sector-benchmark comparisons show words ("Higher than sector median" etc.), not arrow
    glyphs, wherever previously shown.
  - Metric labels render as chips (bordered/filled pill), applied uniformly to every metric.
  - `pytest tests/` green, including new coverage for `attach_assessments`, the health-block
    states (present/absent/partial-null), the flattened metric blocks, and the no-nested-
    details assertion.
  - Real screenshots (Browser pane or the CDP-harness fallback) of all 3 health-block states,
    the consolidated expander with working practice widgets, and the metric chips —
    before/after, reviewed by the owner.
  - scope-auditor (always) + cto-reviewer (`frontend/*`) both PASS on the final staged diff,
    per `.claude/review_routing.json`.

impact_map:
  - Frontend-only change (new fetch/join logic + card rendering restructuring + CSS + docs).
    No backend/pipeline/migration change — `card_assessments` already exists and is already
    populated by Slice 5's merged work; this slice only starts *reading* it. No new
    dependency. Required reviewers (per `.claude/review_routing.json`): **scope-auditor**
    (always) · **cto-reviewer** (`frontend/*`, `tests/*`). Neither analytics-engineer nor
    data-engineer nor equity-analyst-reviewer route to this diff (no `*.sql`/dbt/`supabase/*`/
    `ingestion/*`/`metric_catalogue.csv`/`data_contract.md`/`metric_layer.md` touched).
  - Also subject to the project's **UX PR gate** (`docs/working_agreement.md`) — this IS a
    layout/content change (unlike 6a/6b's pure-skin work), so the gate's mobile-wireframe and
    "one primary job" requirements apply in full, not just as a habit.

amendments:
  - **MEDIAN_PRIMER wording (owner-approved this session):** the round-1 scope-auditor review
    flagged that `frontend/card_copy.py`'s `MEDIAN_PRIMER` string had its arrow-glyph legend
    clause ("↑ higher than median · ↓ lower than median · → at median") removed during
    implementation, with no recorded authority — only `_BENCHMARK_INDICATOR_LABELS` was
    named as pre-approved copy in `explicitly_not_in_scope`. The removal itself was correct
    (the per-metric lines below it already show words, not arrows, so the legend described a
    visual encoding the card no longer uses) — owner reviewed and approved keeping the fix.
    `MEDIAN_PRIMER` now reads only "Median = the middle value among eligible companies in
    this sector and market."
  - **VERDICT_MEANING dropped (owner-approved this session):** the round-1 cto-reviewer flagged
    that `VERDICT_MEANING` (specified in `technical_definition` above, originally) plus its
    `tests/tooling/` sync-guard test shipped with zero consumers — nothing in this slice's UI
    renders that sentence (the badge shows only `VERDICT_BADGE_LABEL`; the AI-read paragraph
    is separate free text). Owner decided: drop both the dict and the guard test now (YAGNI);
    re-add exactly when a real consumer needs it. Done — `VERDICT_MEANING` and
    `tests/tooling/test_card_copy_verdict_sync.py` removed from this diff.
  - **Dead `benchmark_indicator()`/`_BENCHMARK_INDICATORS` (owner-approved this session):** the
    round-1 cto-reviewer flagged that this diff removes the last production caller of the
    arrow-glyph function `benchmark_indicator()` (superseded by `benchmark_indicator_label()`),
    leaving it and its dict dead — but the only remaining reference is
    `tests/frontend/test_benchmark_indicators.py`, outside this contract's `scope_paths`. Owner
    decided: leave it deferred to the already-spawned separate follow-up task rather than widen
    this diff's scope this late in review. Not fixed here — tracked separately.
