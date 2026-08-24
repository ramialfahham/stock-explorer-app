# Task contract

objective: **Three combined, owner-approved changes to the card metric cell and stack:**
  (1) generalize the direction cue (". Higher/Lower is better.") from the 5 benchmarked
  metrics to every catalogued metric with a known `direction`; (2) redesign the range
  mark's layout — numbers row above the bar, word labels ("min"/"median"/"max") below it,
  replacing the old inline `min X%`/`max X%` text-prefix design; (3) surface the metric
  catalogue's existing `perspective` (lens) grouping as visible section headings in the
  metric stack, on both the card face and the learn panel — previously used only for
  silent sort order. Raised by the owner reviewing the live app after MR #22 shipped: a
  UI-form question ("metrics without bullet graph?"), two layout requests ("two rows,"
  "make the grouping visible"), and a repeated, strongly-worded UX complaint about learn-
  panel scroll length. Iterated through several mockup rounds (`mcp__visualize__show_widget`)
  before "implement it," then generalized further mid-implementation via the owner's own
  ceteris-paribus reasoning from MR #22 ("Ceteris paribus, we can say everywhere higher /
  lower is better").

scope_paths:
  - frontend/card_copy.py            # metric_direction(), metric_perspective_label(),
                                      # metric_gloss() rewritten for the universal cue
  - frontend/card_ui.py              # _metric_range_html() rewritten for the new layout;
                                      # _metric_stack_with_groups() (new, shared by card
                                      # face and learn panel); _direction_cue() removed
  - frontend/styles.py               # range-mark CSS replaced for the new structure;
                                      # new .ss-metric-group-heading (+ grid-gap-aware
                                      # card-face override)
  - tests/frontend/test_card_ui.py   # range-mark structure, direction-cue integration
                                      # smoke checks, new grouping tests
  - tests/frontend/test_card_copy.py # metric_direction()/metric_gloss()/
                                      # metric_perspective_label() unit coverage
  - docs/ui/card_metric_cell.md      # wireframe, benchmarks section, and metric-stack
                                      # section all described the pre-existing (now
                                      # replaced) mechanism
  - dbt_analytics/seeds/metric_catalogue.csv  # learn-text caveat additions for 3
                                      # metrics (equity-analyst-reviewer round-1 FAIL,
                                      # see amendments) -- added round 2, not round 1
  - frontend/metrics.json            # regenerated from the seed via
                                      # export_metric_definitions_json.py, never hand-
                                      # edited -- added round 2
  - dbt_analytics/models/_docs.md    # {% docs card_metrics %}/{% docs card_eligibility %}
                                      # blocks had general "five metrics" claims (added round 5)
  - dbt_analytics/seeds/_seeds.yml   # importance_tier column description described the
                                      # removed hero/tier visual split (added round 5)
  - docs/product_roadmap_2026-06.md  # one line in its "Verification checklist (each
                                      # release)" section -- a standing procedure, not
                                      # the file's otherwise-archival status content
                                      # (added round 5)
  - frontend/brand.py                # PRODUCT_TAGLINE -- the deferred onboarding-copy
                                      # item (task_21931170), owner asked for it back
                                      # in scope directly in conversation (added round 5)
  - frontend/landing.py              # onboarding "How it works" bullet, same owner ask
  - frontend/overflow_menu.py        # MENU_METRICS_LINE, _SEARCH_TIP, and
                                      # right_now_line()'s Search-tab string -- all 3
                                      # found via a repo-wide sweep after fixing the
                                      # first 2 the owner named directly
  - tests/frontend/test_overflow_menu.py  # 2 tests asserting the old exact strings
  - dbt_analytics/models/4_intermediate/_intermediate.yml  # int_stock__card_metrics'
                                      # model-level description said "five swipe-card
                                      # metrics" (added round 5)
  - docs/ui/discover_header.md       # "About the data" expander spec cited the old
                                      # "five-metric gate" wording (added round 5)
  - README.md                        # top-level Highlights bullet + architecture
                                      # diagram label, both general "five-metric"
                                      # claims (added round 5)
  - docs/metric_layer.md             # "int_stock__card_metrics computes the five
                                      # metrics" -- now computes every catalogued
                                      # metric, per type (added round 5)
  - docs/working_agreement.md        # 480px smoke checklist's "three hero metric
                                      # values" line -- same staleness pattern already
                                      # fixed twice in north_star.md, missed here until
                                      # scope-auditor round 4 (added round 4)
  - docs/data_contract.md            # market-activation coverage-audit step said "all
                                      # five metrics" -- same pattern, self-found while
                                      # fixing the round-4 finding above (added round 4)
  - docs/development_workflow.md     # identical coverage-audit line, same fix (added
                                      # round 4)
  - docs/north_star.md               # "five mandatory metrics" section contradicted
                                      # this task's own card_metric_cell.md rewrite
                                      # (scope-auditor round-1 FAIL) -- added round 2
  - .claude/task/contract.md

decisions_reserved (owner-approved this session, in conversation):
  - **Reopening the range mark's layout again**, after MR #22 shipped it — owner-
    initiated ("numbers for min max and median are really small" during MR #22's own
    Verify step; this task's own layout requests came after that shipped).
  - **Two-row split**: numbers above the bar, word labels below — owner, after two
    interim mockups ("min max median text looks cluttered," "both look even more
    cluttered") were rejected: "min max median as text below the bar, the numbers above
    the bar."
  - **Min/median/max share one alignment rule** — owner caught an inconsistency in an
    interim mockup ("median and number center aligned where the gap is. min and max and
    numbers center align were the ends of the bars are") after an edge-anchored draft
    made the max label visibly drift from its own tick.
  - **The two-segment gap bar stays** — owner caught a regression ("you dropped the gap
    in the bar") when an interim redesign draft replaced it with a plain solid bar.
  - **Lens grouping made visible**, both card face and learn panel — owner: "we had a
    grouping for all these metrics. we should apply the grouping in the app as well,"
    after confirming the existing `perspective` catalogue field / `_LENS_ORDER` sort was
    real but invisible.
  - **Direction cue generalized to every metric, not just the 5 benchmarked ones** —
    owner, mid-implementation: "Ceteris paribus, we can say everywhere higher / lower is
    better," extending MR #22's own resolution of the same question (there, scoped to
    forward P/E specifically; here, generalized to the full catalogue). Explicitly not a
    re-litigation of that decision — same reasoning, wider application.
  - **Endless-scrolling learn-panel complaint**: raised again this session, strongly
    worded ("This is terrible UI/UX. We have not resolved this yet"). Addressed
    indirectly by this task's grouping (headings break the list into scannable
    sections) but not by shortening or restructuring the panel itself — see
    explicitly_not_in_scope. Flagging the distinction explicitly so shipping this task
    is not mistaken for having resolved the underlying complaint.
  - **`docs/north_star.md` fixed now, as part of this task** ("Go with A") — the owner's
    explicit choice between two conflicting paths presented at escalation (fix the
    contradicting doc now vs. defer both it and the newly-discovered live onboarding-
    copy issue together). The onboarding copy itself stays deferred, spawned as a
    separate task (`task_21931170`) — see explicitly_not_in_scope.
  - **Equity-analyst-reviewer's 4-metric FAIL: "proceed with your recommendations"** —
    owner-approved the assessed-per-metric approach (value-aware branch for
    `debt_to_equity`, mirroring the existing `net_debt_to_ebitda` pattern; learn-text
    caveat additions for `revenue_growth_yoy_pct`/`current_ratio_stmt`/
    `statement_roe_pct`) without requiring a further round to approve exact wording
    first — see amendments for the drafted text and the reasoning for treating
    `statement_roe_pct` differently from `debt_to_equity` despite both having a
    negative-equity failure mode.
  - **Gloss-line spacing** ("too close to the number or to the bullet graph") and **a
    placeholder for the no-range-mark gap** ("if there is no bullet graph it still
    looks like a bug... 'No benchmarking available.' (you may rephrase it)") — both
    owner-initiated this round, not reviewer findings. Placeholder wording rephrased to
    "No sector comparison for this metric." (owner explicitly invited rephrasing).
  - **The deferred onboarding-copy fix (`task_21931170`), pulled back into this task's
    scope directly by the owner** ("There is still this tagline...") — the owner
    flagged the still-stale `PRODUCT_TAGLINE` after the doc-level "five metrics"
    staleness had been swept everywhere else; presented 3 concrete before/after
    proposals (one per stale string then known: tagline, onboarding bullet, search
    tip) for approval rather than drafting silently, given this is explicitly
    user-visible product wording (§6). Owner: "yes, go ahead." The task_21931170 chip
    is now redundant with work already done here — dismissed, not left standing as a
    stale duplicate.
  - **The 2 self-found `overflow_menu.py` strings, approved retroactively after
    scope-auditor round 6 correctly caught that they'd shipped without the same prior
    review as their 3 siblings.** Presented the same before/after table used for the
    original 3; owner: "yes, go ahead." The content itself was fine (matches the
    approved pattern exactly, both em-dash-free); the process gap was real, not just
    a technicality the reviewer manufactured — implementing first and disclosing after
    is not prior approval, and "same file, same category, seems obviously fine" is
    exactly the self-authorization-by-analogy the working agreement's own meta-rule
    (§6) names and rejects. No code change needed to close this finding, since the
    strings were already correct; the process is what needed fixing, and did.

technical_definition:
  - `card_copy.py`: `_PERSPECTIVE_BY_METRIC` / `metric_perspective_label()` — title-cased
    catalogue `perspective`, `""` for an unrecognized metric id (defensive). New
    `_DIRECTION_BY_METRIC` covers all 16 catalogued metrics (vs. the old
    `_DIRECTION_SHORT`-via-`BENCHMARK_METRICS` path, which only covered the 5
    benchmarkable ones) / `metric_direction()`, `"neutral"` for an unrecognized id
    (no catalogued metric is actually `neutral` today — 11 `higher_better`, 5
    `lower_better` — the fallback exists for safety, not because it's exercised).
    `metric_gloss()` appends `". Higher is better."` / `". Lower is better."` for every
    metric with a known direction, unconditionally on range-mark availability (the
    generalization) — still suppressed only for `net_debt_to_ebitda`'s value-aware "Net
    cash" branch, still appends after the alternate `ebit_margin_pct` annual-basis base
    text.
  - `card_ui.py`: `_range_point_html(row_class, left, text)` — one min/median/max entry;
    all three render through the *same* class (`ss-metric-range-number` /
    `ss-metric-range-word`), only the inline `left` differs, centered via a shared CSS
    `transform: translateX(-50%)` (replaces three previously-separate per-role classes).
    `_metric_range_html()` rewritten: numbers row, then the track (bar + gap + marker,
    mechanism unchanged from MR #22), then a words row. Min/max fixed at `0%`/`100%`;
    median's *label* position (numbers and words rows both) clamped via
    `clamp(3rem, {median_pct}%, calc(100% - 3rem))`, identical mechanism to MR #22, now
    reused for two rows instead of one. `_direction_cue()` removed — folded into
    `card_copy.metric_gloss()` since the cue is no longer range-mark-specific.
    `_metric_stack_with_groups(card, cell_fn)` (new): walks `metrics_for_card(card)`
    (already lens-sorted since MR #22's Router work), inserts one
    `<p class="ss-metric-group-heading">` per lens transition, calls `cell_fn` per
    metric. Shared by `build_card_html()` (card face, `cell_fn=_metric_cell_html`) and
    `_metric_learn_blocks()` (learn panel, `cell_fn=_metric_learn_block_html`, extracted
    from the former inline loop) — one implementation, both surfaces group identically
    by construction, not by keeping two copies in sync.
  - `styles.py`: range-mark CSS fully replaced (three-row structure: `.ss-metric-range-numbers`/
    `-number`, `.ss-metric-range-track`/`-bar*`/`-marker` repositioned, `.ss-metric-range-words`/
    `-word`). New `.ss-metric-group-heading` — plus a card-face-scoped override
    (`.ss-metrics-stack .ss-metric-group-heading`) discovered necessary during Verify:
    the card face lays metrics out on `display: grid; gap: 0.95rem`, so a heading's own
    `margin` adds to (not replaces) that gap — the base rule alone produced a lopsided
    ~1.85rem gap above headings vs ~1.3rem below. The scoped override uses a smaller
    positive `margin-top` (deliberate section break, still additive to the grid gap) and
    a *negative* `margin-bottom` (claws back part of the grid gap so the heading reads
    as attached to its group) — verified live (see done_when) rather than assumed correct
    from reading the CSS.
  - **Round 2** (post-review fixes, see amendments for the findings that drove each):
    `.ss-metric-range-number` gained `max-width: 5rem; overflow: hidden; text-overflow:
    ellipsis` (cto-reviewer FAIL — the old fixed-width-column overflow protection had
    no replacement in the new absolutely-positioned design). `card_copy.py` gained a
    `debt_to_equity` value-aware branch (gloss/analogy/learn_text), mirroring
    `net_debt_to_ebitda`'s pattern exactly, self-detecting from the ratio's own sign
    since debt is always ≥ 0. `metric_catalogue.csv` gained learn-text caveat sentences
    for `revenue_growth_yoy_pct`, `current_ratio_stmt`, `statement_roe_pct` (no
    em-dashes in any new text, matching the standing "easy to read" rule from MR #22;
    existing em-dashes removed from each field touched, not left standing next to new
    dash-free text). `_metric_range_unavailable_html()` (new, `card_ui.py`) renders
    `"No sector comparison for this metric."` whenever `_metric_range_html()` returns
    `""`, wired into `_metric_cell_html()`. `.ss-metric-gloss`/`.ss-metric-range-
    unavailable` top margin raised `0.1rem → 0.5rem`, and both rescoped from bare
    single-class selectors to `.ss-metric .ss-metric-gloss` / `.ss-metric
    .ss-metric-range-unavailable` after discovering Streamlit's own emotion-cache
    stylesheet resets `<p>` margin-top/left/right at (0,1,1) specificity, silently
    beating a (0,1,0) single-class rule regardless of source order — the fix needed
    (0,2,0)+ specificity, not just "add the margin."

explicitly_not_in_scope:
  - Restructuring or shortening the learn panel itself (collapsing groups by default,
    splitting into multiple panels, etc.) — the owner's "endless scrolling" complaint is
    only partially addressed by this task's grouping (scannable sections, not fewer
    rows); a real fix is a separate, larger UX decision (§6) not implicit in "implement
    it" for this task's three specific changes.
  - Extending `benchmarkable: true` (and therefore the range mark itself) to the 11
    metrics that don't have one today — unchanged from MR #22's own deferral; the
    direction cue's generalization does not require or imply this.
  - The sector min/max data-quality issue surfaced during Verify (ASX Energy's
    `fcf_margin_pct`/`ebit_margin_pct` cohort dominated by one near-zero-revenue
    denominator company, Deep Yellow/DYL) — a dbt-layer metric-definition question
    (owner's call), not a frontend fix; documented in
    `docs/ui/card_metric_cell.md`'s "Known data-quality interaction" so it isn't
    rediscovered from scratch, not acted on here.
  - Any Supabase/CI change, and any dbt change beyond the one seed edit added round 2
    (a `metric_catalogue.csv` text-field update, regenerated straight through to
    `frontend/metrics.json` — no model, schema, or column change). Confirmed by running
    the full test suite (`tests/`, not just `tests/frontend/`) green.
  - The live onboarding-copy inaccuracy discovered via the `north_star.md` fix
    (`frontend/brand.py`'s tagline, `frontend/landing.py`, `frontend/overflow_menu.py`
    all still assert "five financial fundamentals," wrong for all 3 company types since
    the Router shipped) — owner's explicit "Go with A" choice: fix the doc now, defer
    the app copy itself. Spawned as `task_21931170`, not touched here.
  - A full pipeline fix for `statement_roe_pct`'s negative-equity/loss false-positive
    (would need a new raw equity-sign field exposed through
    `dbt_analytics` → `scripts/export_to_supabase.py` → the frontend) — out of
    proportion for a frontend-only task; given the same learn-text-caveat treatment as
    the two oversimplification-only findings instead. See amendments and
    `docs/ui/card_metric_cell.md`'s value-aware gloss table for the reasoning.

done_when:
  - All three changes render correctly against the real app (local Streamlit + live
    Supabase) via the Browser pane: universal direction cue, new range-mark layout, and
    visible lens-group headings on both the card face and the learn panel.
  - Range-mark label collision/overflow verified against every real range-mark row
    currently in production (3,967 rows across all 5 benchmarked metrics, via direct
    read-only Postgres query + the actual `benchmark_range()`/`format_metric_value()`
    functions), not just spot-checked — including the most extreme real outlier
    (Deep Yellow, -129,810.5% FCF margin) — plus synthetic cases beyond today's real
    spread to stress the median-label clamp specifically.
  - Group-heading spacing verified against live computed geometry (not assumed from
    the CSS): a clearly larger gap above a new group than between two metrics in the
    same group, and a tight gap between a heading and its own group.
  - Full test suite green (`tests/`, all 200+ tests, not just the frontend subset).
  - `docs/ui/card_metric_cell.md` updated — wireframe, benchmarks mechanics, and the
    metric-stack section all describe the shipped design, not the one it replaced.
  - Required reviewers, staged-diff hash matching the final round-2 diff (the round-1
    diff was reviewed and FAILed by all 3 dispatched reviewers — see amendments; the
    hash in `review.md` covers what actually gets committed, not that intermediate
    state): scope-auditor (always); cto-reviewer (`frontend/*`/`tests/*`);
    **analytics-engineer-reviewer** (`*.csv`, mechanically triggered round 2 by the
    `metric_catalogue.csv` edit — not required round 1, when the diff was frontend-only).
    **Plus equity-analyst-reviewer, dispatched deliberately beyond what
    `.claude/review_routing.json` mechanically triggers round 1** (round 2 it's also
    mechanically triggered via `*metric_catalogue.csv`, so the deliberate-dispatch
    reasoning only mattered for round 1's diff) — the direction-cue generalization is a
    financial-content-reasoning change in substance, in this reviewer's domain
    regardless of which file it landed in. Concretely: `dividend_yield_pct` is
    catalogued `higher_better`, yet an unusually high yield is a known equity-analysis
    distress signal, not straightforwardly "better" — the same shape of
    oversimplification risk that triggered this reviewer's scrutiny (and an owner
    escalation) for forward P/E in MR #22. The owner's ceteris-paribus instruction
    already settles *whether* this generalization is authorized (§6, not re-litigated
    here); this dispatch is about catching execution mistakes in scope, not re-asking
    the settled question. Same class of gap as the `.claude/review_routing.json` file's
    own documented tension around `data-engineer-reviewer`/`supabase/*` — flagged, not
    silently patched into the routing config itself (that's a permanent-rule change,
    owner's call).

impact_map:
  - User-facing: every card on the Discover/Search/Saved surfaces — the direction cue
    and grouping apply to every metric on every card (all company types), not just the
    5 benchmarked metrics the range-mark layout change touches.
  - The round-3 writing-voice pass widens this further: `SECTOR_GLOSS`
    (`frontend/card_copy.py`) renders on every single card regardless of which metrics
    it shows, so its 11 rewritten entries are the single highest-frequency text change
    in this task, despite not being metric-cell content at all.
  - No data, schema, or pipeline change — pure frontend rendering of data that was
    already being exported; no new column, no new eligibility rule, no change to any
    stored value. **Correction (analytics-engineer-reviewer round 3):** this bullet
    previously named `calculation` in the same breath as `direction`/`perspective`/
    `benchmarkable`/`applies_to` as unchanged — wrong, and self-contradicting the
    adjacent sentence naming `calculation` as one of the round-3 voice-pass's touched
    prose columns. The distinction that actually matters: `calculation` (and
    `description`/`interpretation`/`applicability`) are prose *describing* the metric,
    touched deliberately this round for tone; `numerator_expr`/`denominator_expr`/
    `base_relation`/`format`/`direction`/`perspective`/`benchmarkable`/`applies_to`/
    `importance_tier`/`display_order`/`basis_column` are the columns that actually
    drive app behavior or dbt logic, independently re-verified byte-identical across
    all 16 rows by the reviewer, not just claimed.

amendments:
  - **Round 1 review: all 3 dispatched reviewers FAILed.** Summarized here; each
    resolution is detailed in its own bullet below.
    - cto-reviewer: the new absolutely-positioned range-mark labels dropped the old
      design's `overflow: hidden; text-overflow: ellipsis` protection against unbounded
      sector-aggregate outliers (added by this same reviewer role in MR #22 round 3/4
      for exactly this failure mode), with no replacement and no test covering a
      long/extreme value. Fixed.
    - equity-analyst-reviewer (dispatched deliberately, see done_when): the direction-
      cue generalization's execution missed 4 metrics where the catalogue's own
      `applicability`/`interpretation` text already contradicts a flat "Higher/Lower is
      better." claim, with nothing on the card saying so. Fixed for 3, given the
      narrower learn-text-only treatment for the 4th (`statement_roe_pct`) — see below.
    - scope-auditor: `docs/north_star.md`'s "five mandatory metrics" table (a 5-metric,
      hero-three framing) directly contradicts this task's own `card_metric_cell.md`
      rewrite (7 lenses, up to 16 metrics, no hero/tier split) — pre-existing staleness
      from several already-merged Router slices, but this task's diff is what made the
      contradiction explicit for the first time. `north_star.md` itself claims final
      authority on user-facing behavior and isn't in `scope_paths`. Escalated (§6/§7,
      two-path choice); owner picked "Go with A" — fix now. A secondary, weaker finding
      (the words-row's specific type treatment — uppercase, muted, a distinct size —
      not explicitly recorded as owner-approved) was flagged as non-blocking and not
      independently actioned; it's a reasonable implementation of the approved row
      *structure*, and no rendering issue was found with it. **Correction, see below:**
      this "no rendering issue found" characterization turned out wrong — the owner
      caught it directly shortly after (uppercase specifically, unprompted), and it was
      fixed. Recorded honestly rather than left standing.
  - **cto-reviewer's overflow-protection FAIL — fixed and re-verified.** Added
    `max-width: 5rem; overflow: hidden; text-overflow: ellipsis` to
    `.ss-metric-range-number`. Re-verified against real production data (the DYL
    -129,810.5% outlier renders unchanged, ~60px, comfortably under the cap) and a
    synthetic 100x-more-extreme case (confirms the ellipsis backstop actually engages).
    This specific overflow-cap behavior is a CSS property, not independently unit-
    tested beyond confirming the class attaches (structural regression coverage for the
    range mark already exists from round 1) — the live-data verification is the actual
    coverage here, same methodology as the original median-clamp verification. This is
    a bounded cap, not an unconditional
    guarantee — see `docs/ui/card_metric_cell.md`'s Range mark mechanics section for
    why a fully collision-proof cap isn't possible without clipping ordinary
    (non-outlier) values too.
  - **Equity-analyst-reviewer's 4-metric FAIL — resolved per owner's "proceed with your
    recommendations."** Verified all 4 citations against `frontend/metrics.json`
    directly before presenting (each checked out exactly as quoted). Two different fix
    patterns, chosen per whether the failure mode is self-detecting from the metric's
    own value:
    - `debt_to_equity`: value-aware branch (gloss/analogy/learn_text), mirroring
      `net_debt_to_ebitda`'s existing "Net cash" pattern. Self-detecting because debt is
      always ≥ 0, so a negative ratio structurally means equity itself went negative —
      no new data needed. Cue suppressed on this branch (same reasoning as net debt:
      appending "Lower is better." on top would imply a more negative number is a
      *better* version of the same good news, when it's a different, broken state).
    - `revenue_growth_yoy_pct`, `current_ratio_stmt`: learn-text caveat sentences added
      to `metric_catalogue.csv`, mirroring forward P/E's MR #22 fix pattern (deep-dive
      explanation, not the short gloss). No em-dashes in the new text; pre-existing
      em-dashes in the touched fields removed too (same field-wide cleanup precedent as
      forward P/E's fix).
    - `statement_roe_pct`: same learn-text-caveat treatment, **not** the value-aware
      pattern, despite having the same underlying failure shape (a loss over negative
      equity reads as a spuriously positive %). Checked whether it was self-detecting
      the same way as `debt_to_equity` first: it is not — `stmt_net_income_common` and
      `stmt_stockholders_equity` are both used inside the ratio
      (`dbt_analytics/models/4_intermediate/int_stock__card_metrics.sql:188-193`), but
      only their ratio reaches the frontend, and a positive ROE% is structurally
      ambiguous between "genuinely profitable" and "loss ÷ negative equity" — the sign
      alone can't distinguish them, unlike debt_to_equity where debt's own sign is
      fixed. A real fix needs a new raw equity-sign signal exposed through the pipeline
      (`dbt_analytics` → `scripts/export_to_supabase.py` → the frontend) — out of
      proportion for a frontend-only task, so it got the narrower fix (existing
      `learn` text already had a generic "stops being meaningful" hedge; replaced with
      the specific false-positive mechanism instead, matching equity-analyst-reviewer's
      own critique that the generic version wasn't specific enough).
    Re-verified via `metric_gloss()`/`metric_analogy()`/`metric_learn_text()` unit tests
    plus `build_card_html()`/`build_learn_panel_body_html()` end-to-end for the
    `debt_to_equity` negative case (both card face and learn panel).
  - **Own mistake, caught before it reached review: a CSV row corruption.** The
    `revenue_growth_yoy_pct` learn-text edit (replacing an em-dash with ", so")
    introduced a comma into a `metric_catalogue.csv` field that had zero commas in its
    original text and was therefore stored **unquoted** in the raw file — the new comma
    read as a field separator, shifting the row's later columns (`applies_to` absorbed
    part of the new sentence). `current_ratio_stmt`/`statement_roe_pct`'s edits were
    safe because those fields already contained commas and were therefore already
    quoted. Caught immediately by `tests/tooling/test_metric_catalogue.py` and
    `test_assessment_rules.py` (both validate `applies_to` against a fixed company-type
    set) on the very next full test run — not caught by inspection first. Fixed by
    wrapping the field in `"..."` directly in the raw CSV text (the field itself has no
    internal `"` characters, so no escaping needed beyond the wrapping quotes);
    re-parsed and spot-checked all 4 touched rows' later columns before regenerating
    `metrics.json`. Recorded as a memory
    (`csv-field-quoting-risk`, user-global) since the failure mode (raw-text edit adding
    a comma to a field that wasn't already quoted) is specific to this file's editing
    pattern and not obviously avoidable by inspection alone.
  - **Scope-auditor's `north_star.md` FAIL — fixed per owner's "Go with A."** Verified
    the actual eligibility gate (`int_stock__card_metrics.sql:271-286`) before rewriting
    anything: operating's `is_card_eligible` genuinely still requires the same 5
    metrics (so "five mandatory metrics" wasn't wholly fabricated, just no longer the
    *displayed* count, and no longer true for financial/pre_revenue's own, different,
    eligibility gates). Rewrote the section as principle + pointer to
    `card_metric_cell.md`/`data_contract.md` rather than a new hardcoded table, since a
    second hardcoded table is exactly the failure mode being fixed. Also fixed
    `card_metric_cell.md`'s own "Authority" line, which cited the *old*
    "five fundamentals, priority order" framing — missed in the original round-1 write,
    caught while fixing the sibling doc, same class of gap as the anti-pattern this
    project already tracks (sweep for contradicting prose across the whole repo when a
    fact changes, not just the one file the fact "belongs" to).
  - **Discovered, not fixed here: the same "five fundamentals" claim is live app copy,**
    not just stale docs — `frontend/brand.py`'s `PRODUCT_TAGLINE`,
    `frontend/landing.py`'s onboarding bullet, and `frontend/overflow_menu.py`'s search
    tip all assert it, and none of the 3 company types display exactly 5 metrics
    anymore. Owner's explicit "Go with A" scoped this task to the *doc* fix only;
    spawned `task_21931170` for the copy itself (rewriting a product tagline is
    user-visible wording, owner's call, not something to fix silently mid-task).
  - **Discovered and fixed proactively, not from a reviewer finding: a Streamlit CSS-
    specificity gotcha that would have silently defeated the round-2 gloss-spacing
    fix.** `.ss-metric-gloss`'s margin-top change (`0.1rem → 0.5rem`, owner feedback
    "too close to the number or to the bullet graph") measured as `0px` computed, not
    `8px`, on first live verification. Root cause: Streamlit's own emotion-cache
    stylesheet carries a `<hash> p { margin-top: 0; margin-left: 0; margin-right: 0; }`
    reset at (0,1,1) specificity, beating a same-order (0,1,0) single-class rule
    regardless of which loads later. `.ss-metric-range-unavailable` (also a `<p>`, new
    this round) had the identical bug. Fixed by scoping both under `.ss-metric` for
    (0,2,0) specificity; re-verified live (every gap now a consistent 8px, both
    value→mark/placeholder and mark/placeholder→gloss). Spawned `task_b1da0f29` to
    check whether other pre-existing single-class `<p>` rules in `styles.py` have the
    same latent bug — not audited here, out of proportion for this task's scope, but a
    real and non-obvious risk pattern worth someone checking deliberately rather than
    finding the next instance by accident.
  - **Round 2 review: cto-reviewer, equity-analyst-reviewer, and scope-auditor all
    FAILed again; analytics-engineer-reviewer (newly required by the `*.csv` edit)
    PASSed.** Each finding and its resolution is its own bullet below. Two full FAIL
    rounds in a row is exactly the pattern issue #5 flags as too many — noted, not
    dismissed; the volume this round came from a genuinely wide sweep (equity-analyst-
    reviewer and scope-auditor each independently re-checked the full 16-metric
    catalogue and the whole of `north_star.md` rather than re-verifying only what round
    1 touched), which is why it surfaced more than it created.
  - **cto-reviewer round 2, finding 1 — fixed.** `.ss-metric-group-heading`'s base rule
    (bare single class) still carried `font-size`/`margin` directly, the exact
    Streamlit-override shape the round-2 gloss fix had just diagnosed and fixed for two
    *other* classes, left unfixed on this third one. The learn-panel context
    (`.ss-metric-learn-list .ss-metric-group-heading`) had no scoped override at all
    (round 2's contract said this was added; it was planned but not yet applied when
    the round-2 diff was staged for review — a real gap, not a documentation error).
    Fixed: `font-size` and `margin` both moved out of the bare class into two properly
    scoped rules (`.ss-metrics-stack .ss-metric-group-heading` for the card face,
    `.ss-metric-learn-list .ss-metric-group-heading` for the learn panel), each now
    correctly at (0,2,0)+ specificity. Verified live: both contexts now compute
    `font-size: 10.88px` (was silently `16px`, browser default, in both) — this means
    every group heading rendered oversized from the moment they were first added,
    through every earlier live-browser check this task did, because those checks only
    verified spacing/gaps, never the text's own computed size.
  - **cto-reviewer round 2, finding 2 — fixed.** The contract's amendments claimed the
    `debt_to_equity` negative-equity branch was verified "end-to-end... both card face
    and learn panel," but no test called `build_card_html()`/`build_learn_panel_body_html()`
    with a negative value; only the unit-level `metric_gloss()` tests existed. A real,
    if honest, false-completeness claim in the review record. Fixed: added
    `test_build_card_shows_negative_equity_gloss_for_debt_to_equity` and
    `test_learn_panel_shows_negative_equity_analogy_and_learn_text_for_debt_to_equity`
    to `tests/frontend/test_card_ui.py`. Both failed on first write (an unrelated bug in
    the *tests themselves*: asserting the raw apostrophe in "isn't"/"owners'" against
    HTML output, where `_esc()` renders it as `&#x27;` — fixed by using escape-safe
    substrings) before passing.
  - **Equity-analyst-reviewer round 2, finding 1 — fixed.** The `revenue_growth_yoy_pct`
    caveat added in round 2 covered only half of the metric's own catalogued
    `applicability` risk ("growth ≠ health"), missing the other named risk ("Distorted
    by tiny prior-year bases... huge % off a small base") — the same near-zero-
    denominator distortion this task's own "Known data-quality interaction" note
    already documents as live in production for a sibling metric. Fixed: extended the
    `learn` field with a second sentence naming the small-base risk directly ("A small
    prior-year base can also inflate the percentage sharply, so a very large number
    here does not always mean strong momentum"). Caught as still-missing a second time,
    after the catalogue-voice-pass bullet below was first written claiming it was
    already done when it wasn't; corrected before finalizing rather than left as an
    inaccurate record.
  - **Equity-analyst-reviewer round 2, finding 2 — acknowledged, not fixed (code
    change), per the reviewer's own framing.** `debt_to_equity`'s `value < 0` check
    doesn't catch every negative-equity case: when `stmt_total_debt` is exactly `0` and
    equity is negative, the ratio computes to exactly `0.0` (zero over any nonzero
    denominator), which fails the `< 0` test — the "negative ratio always means negative
    equity" claim is sound in one direction (no false positives) but incomplete in the
    other (some negative-equity cases at exactly zero debt go undetected). Confirmed
    this isn't fixable from the ratio alone: `value <= 0` would misfire the other way,
    since debt=0 with *positive* equity (a genuinely debt-free, healthy company) also
    computes to exactly `0.0`, and the ratio can't distinguish the two cases without an
    independent signal — the same underlying limitation as `statement_roe_pct`'s finding
    in round 1. Narrow (needs debt to be *exactly* zero, not merely small) and lower-
    probability than round 1's findings; the reviewer's own framing offered "a one-line
    acknowledgment... if not fixed" as sufficient. This is that acknowledgment.
  - **Scope-auditor round 2, finding 1 — fixed.** The round-2 `north_star.md` fix
    rewrote only the "## The card" section; three more flat "five metrics" claims stood
    unfixed in the *same file* (the doc's own opening definition, the eligibility-gate
    line, and two "hero metric" references in the Progressive Disclosure section that
    describe a hero/tier visual split this task's own design removed). The round-2
    amendment's claim to have applied "the anti-pattern this project already tracks
    (sweep for contradicting prose across the whole repo...)" was itself inaccurate — it
    didn't even cover the rest of the one file being edited. Fixed: all remaining
    instances corrected (see the file for exact wording); the mobile "success check"
    line specifically was softened to not assert a now-unverified claim (how many metric
    values fit above the fold at the new, larger per-type counts) rather than either
    keep a false claim or silently investigate a UX question that's genuinely out of
    scope for a doc-accuracy fix.
  - **Scope-auditor round 2, finding 2 — fixed.** The round-2 rewrite's own replacement
    text ("the exact per-type metric lists live in `card_metric_cell.md` and
    `data_contract.md`") was itself inaccurate for both citations: `card_metric_cell.md`
    explicitly disclaims having a hardcoded list (by design, to avoid exactly this kind
    of drift), and `data_contract.md` only documents the *required* (eligibility) sets,
    not the *full displayed* sets the new text was distinguishing. Fixed: corrected to
    state plainly that the full displayed set isn't enumerated in any doc,
    `metrics_for_card()` is the sole authoritative source, and only the required sets
    live in `data_contract.md`.
  - **Scope-auditor round 2, findings 3 and 4 — checked, no content change needed,
    audit-trail gap closed.** Flagged `dividend_yield_pct` and `price_to_tangible_book`
    (both catalogued directions with a known oversimplification risk per their own
    `interpretation`/`applicability` text) as unverified — notably, `dividend_yield_pct`
    is the metric the contract's own `done_when` section cites *by name* as the
    motivating example for dispatching equity-analyst-reviewer at all, yet was never
    actually checked. On inspection: both already carry the caveat in their `learn`
    field, pre-existing from before this task, already matching the established
    gloss-stays-flat/learn-carries-the-caveat pattern (the owner's own stated principle
    from MR #22 — "We should address these things in the metric explanation part").
    Neither has a clean, self-detecting value threshold the way `net_debt_to_ebitda`/
    `debt_to_equity` do (a high yield or a sub-1 P/TB is a probabilistic, contextual
    concern, not a sign-flip), so a value-aware branch isn't the right mechanism even in
    principle. No text changed for these two specifically; the finding's real content
    was closed by verifying rather than by editing. The valid part of the finding — the
    contract cited a risk by name without ever checking it — is a real process gap, not
    a content one; recorded here so the audit trail is honest about it.
  - **Owner feedback, not from a reviewer: three rounds of direct, live UI/UX
    correction, converging on a full catalogue writing-voice pass.** In order:
    (1) "You applied capital letters for min max and median although i did not ask you
    to do it" — `.ss-metric-range-word` had gained `text-transform: uppercase`,
    `letter-spacing`, a smaller font-size, and a different color than the numbers row,
    none of it part of the approved row *structure*. Fixed: matches the numbers row
    exactly now (this directly confirms scope-auditor round 1's "weaker" finding on
    this exact class was right, corrected above).
    (2) A screenshot of the learn panel ("is this all fat fonts... I'm sure there are
    guidelines") led to checking `docs/ui/design_system.md` (confirmed: covers spacing/
    radius/button tokens, silent on a text-weight/color hierarchy) and finding
    `.ss-metric-analogy` styled bold + `--ss-accent` gold — pre-existing from the
    original "Slice 6c" commit (`98cf271`), not introduced this task, but not matching
    the established plain-body-text pattern (`.ss-metric-gloss`, same card, same role)
    either. Fixed to match `.ss-metric-gloss` exactly; this also needed the same
    (0,2,0)-specificity rescoping as the round-2 gloss fix (`.ss-metric-learn-item
    .ss-metric-analogy`) — its `font-size` was independently found to be silently
    reset to browser-default `16px` by a *third* Streamlit rule
    (`.st-emotion-cache-okb1kv p { font-size: inherit; }`, not previously identified).
    A repo-wide regex sweep at this point found the same bare-single-class-on-`<p>`
    shape in ~20 other classes across the app (landing page, menus, saved list, row
    primitives) — all pre-existing, none touched here; `task_b1da0f29` (spawned
    earlier this round) updated to reflect the true scale rather than the original,
    much narrower estimate.
    (3) "bullet graph labeling is really small text and numbers" — asked whether to
    size the bullet-graph text above the app's standard caption size; owner's reply
    ("we had this round already... it's a ping pong") correctly identified that this
    question was already settled in MR #22 (bump to `--ss-caption-size`, the app's
    standard secondary-text token) — the *re-asking* was the mistake, not an open
    question. Not reopened; caption-size stands, unconditionally, going forward.
    (4) `fcf_margin_pct`'s existing analogy field, quoted directly ("The explanations
    MUST NOT [read] like AI generated text... Really bad. I already told you before"),
    led to `AskUserQuestion`: fold a full catalogue-wide writing-voice pass into this
    task now, or defer it. **Owner: now.**
  - **Full catalogue writing-voice pass (owner-approved scope expansion, see above).**
    Two sweeps against every field of all 16 catalogued metrics (not just the fields
    this task's own diff had already touched): (a) every em-dash, in every field
    including the never-rendered `interpretation`/`applicability`/`calculation`/
    `description` columns (`dbt_analytics/seeds/metric_catalogue.csv` had 46 vs. the
    pre-this-task base state; 0 remain, verified by direct character count after every
    write, not just spot-checked), replaced with plain punctuation (comma, colon, period, or a restructured sentence),
    never a different dash-like substitute; (b) hedge-and-pivot AI-voice patterns per
    [[feedback-writing-voice]] (the `"X isn't automatically Y... it can mean A, or B"`
    template specifically) — found and rewritten in `dividend_yield_pct.learn`
    (dropped the "not automatically good" hedge frame, stated the two alternative
    readings directly) and tightened in this task's own `current_ratio_stmt.learn`/
    `statement_roe_pct.learn` additions from round 1. `revenue_growth_yoy_pct.learn`
    also picked up the missing small-base-distortion sentence here (equity-analyst
    round 2, above) as part of the same pass. Extended to `frontend/card_copy.py`'s
    hardcoded, genuinely-rendered strings in the same two sweeps: `SECTOR_GLOSS` (11
    entries, always visible on every card face), `BENCHMARK_COMPARE_UNAVAILABLE_LEARN`,
    and the `net_debt_to_ebitda`/`ebit_margin_pct` value-aware gloss/analogy/learn
    branches (5 strings). Every touched test/doc that quoted an old exact string
    (`"Net cash — cash on hand exceeds debt"` in `test_card_copy.py` ×2,
    `test_card_ui.py` ×1, `docs/ui/card_metric_cell.md` ×1) updated to match. **Not
    extended to:** Python docstrings/code comments (never rendered, not what "reads
    like AI" was about) and this contract's own already-written amendment history
    (a chronological log, not polished prose; new amendments are written dash-free
    going forward, already-recorded ones aren't retroactively rewritten to avoid
    introducing transcription risk into what's meant to be an accurate record). Two new
    persistent memories written recording the corrected, current scope of the "no
    em-dashes" rule (superseding an earlier, narrower characterization) — see
    [[no-em-dashes-anywhere]].
  - **CSV editing safety, applied this round.** Given this pass touched 14-15 of 16
    catalogue rows (not the single-line edits `git diff --stat` shows for round 1's
    3-field change), used a programmatic `csv.DictReader`/`DictWriter` round-trip
    instead of the manual raw-text `Edit` calls round 1 used (and which corrupted a row
    that round, see the earlier amendment) — safer at this scale, at the cost of
    accepting Python's `csv` module may normalize quoting on fields it rewrites
    (content-inert, same class of byproduct as the CSV-quote-stripping incident in MR
    #22, not a new risk). Verified after every write: row count, `applies_to`/
    `direction` enum well-formedness, zero remaining em-dashes, full test suite green,
    `metrics.json` regenerated and consistent.
  - **Round 3 review: all 4 reviewers dispatched; equity-analyst-reviewer, scope-
    auditor, and analytics-engineer-reviewer FAILed; cto-reviewer PASSed.** Each below.
  - **Equity-analyst-reviewer round 3 — fixed.** The writing-voice pass's rewrite of
    `current_ratio_stmt.applicability` (never rendered to users, but still catalogue
    content) dropped the explicit "is not automatically good" corrective clause when
    simplifying the sentence, leaving only a softer "can mean X" framing — the same
    hedge-removal the pass deliberately applied to `dividend_yield_pct.learn`, but
    applied here by oversight, not intent, and with no corresponding disclosure.
    Mitigated by the fact that `applicability` is never rendered (confirmed: no call
    site reads it) and the parallel, rendered `learn` field for this same metric kept
    the equivalent caveat throughout — so this never reached a user — but the finding
    stands as a real meaning-drift the process is supposed to catch. Fixed: restored
    the explicit "is not automatically good" framing, dash-free
    ("...is not automatically good, since it can mean cash sitting idle."). **This
    specific edit corrupted the CSV a second time** (see the dedicated amendment
    below) — caught and fixed before this bullet was finalized, not left standing.
  - **Own mistake, repeated: a second CSV corruption from a raw-text edit, this
    session.** Despite the `csv-field-quoting-risk` memory written after round 2's
    identical incident, fixing the equity-analyst finding above via a direct `Edit`
    call (not the safer `DictReader`/`DictWriter` round-trip used for the bulk voice
    pass) introduced a new comma into `current_ratio_stmt.applicability` without
    checking whether that field was already quoted in the raw file. It wasn't quoted
    (no prior comma in the original text), so the new comma shifted the row exactly
    as before, breaking `int()` parsing on `importance_tier` (which received the
    string `"liquidity"`, that row's `perspective` value, shifted one column over).
    Caught immediately by the same full-test-suite run this whole process now runs
    after every catalogue edit (4 failures, `ValueError: invalid literal for int()...
    'liquidity'`), not by inspection. Fixed by wrapping the field in `"..."` directly,
    matching the round-2 recovery pattern exactly. Re-verified: 16/16 rows parse, all
    structural columns well-formed, 206/206 tests pass. The `csv-field-quoting-risk`
    memory's own guidance held (re-parse and check immediately after any raw-text CSV
    edit) — what failed was applying a manual `Edit` at all for a single-field fix
    when the safer scripted approach was already in hand and should have been reused
    for consistency, not just for edits at the earlier, larger scale it was written for.
  - **Scope-auditor round 3, two findings — both fixed.** `docs/ui/card_metric_cell.md`
    quoted two strings from `frontend/card_copy.py` that this same round's voice pass
    had changed elsewhere in the same diff, missed by the "every touched test/doc
    updated to match" sweep two amendments ago: `BENCHMARK_COMPARE_UNAVAILABLE_LEARN`
    (em-dash quote, line 218, vs. the actual now-colon string) and the `north_star.md`
    "Authority" line's citation of that doc's own section heading (also em-dash quote
    vs. the actual now-colon heading, both sides freshly authored this round). Both
    fixed to match. A third, self-found instance in the same doc while re-sweeping for
    more of the same pattern: a paraphrased "quote" of `north_star.md`'s naive-rankings
    line dropped `"Top 10% in sector"` from the middle while still presenting the
    result in quotation marks as if exact — corrected to an accurately-ellipsized
    partial quote instead of a misquote.
  - **Analytics-engineer-reviewer round 3, two findings.** (1) Fixed: this contract's
    own `impact_map` claimed `calculation` was unchanged in the same sentence that,
    two lines earlier, named it as a touched column — a direct self-contradiction.
    Corrected to distinguish prose-description columns (touched deliberately:
    `calculation`/`description`/`interpretation`/`applicability`) from the columns
    that actually drive behavior (untouched, independently re-verified by the
    reviewer). (2) Investigated, confirmed inert, not fixed as code: the
    `DictWriter` round-trip writes `\r\n` line terminators (the `csv` module's
    default "excel" dialect), flipping the *working-tree* file from the repo's
    original all-LF convention to all-CRLF — a real, previously-undisclosed effect
    the reviewer caught, not a false alarm. Checked what actually reaches git history:
    this repo has `core.autocrlf=true` already configured (pre-existing, not set by
    this task), which normalizes line endings back to LF on `git add`, confirmed by
    directly inspecting the staged blob (`git show :dbt_analytics/seeds/metric_catalogue.csv`)
    — 0 CRLF, matching HEAD's convention exactly, and matching `git diff --stat`'s
    16-line (not full-file) change count. The working-tree artifact is real and the
    reviewer was right to flag it as previously unverified; the actual committed
    history is unaffected, verified directly rather than assumed.
  - **Round 4 review: cto-reviewer, equity-analyst-reviewer, and analytics-engineer-
    reviewer all PASSed (each confirmed the round-3 fix it FAILed on now holds, via
    independent re-verification, not by re-reading this contract); scope-auditor
    FAILed once more, its third consecutive round finding something new.** Given the
    pattern — a new instance of the same "five metrics"/"hero" staleness class every
    round scope-auditor has run so far (north_star.md once in round 1, three more
    spots in round 2, this round a third document) — did a full repo-wide grep for
    the pattern this time (`hero metric|hero three|three hero|five metric|five
    fundamental`, case-insensitive, all file types) rather than fix only the cited
    instance and wait for the next round to find another one.
  - **Scope-auditor round 4 finding — fixed, plus 2 more instances of the identical
    pattern found via the repo-wide sweep above, fixed the same way.**
    `docs/working_agreement.md`'s 480px smoke-gate checklist (CLAUDE.md's own named
    mandatory doc for "Streamlit layout/copy/interaction changes" — the category this
    task is in) still asserted "three hero metric values visible without scroll,"
    identical to the claim already retired twice in `north_star.md`. Fixed, same
    treatment as those two fixes (no false claim about the new, larger per-type
    metric counts; points to the real smoke checklists instead). The sweep also found
    `docs/data_contract.md` and `docs/development_workflow.md` each had one identical
    "coverage audit (all five metrics...)" line, in the market-activation checklist —
    same context and same defensibility as `north_star.md`'s own already-fixed
    markets passage (genuinely about the operating-type eligibility gate, which is
    still 5 metrics, just under-specified as a universal claim); both clarified to
    name the operating-type gate explicitly rather than left as an ambiguous "five
    metrics." **Checked and deliberately left alone:** `docs/product_roadmap_2026-06.md`
    (explicitly dated, "Last refreshed: 2026-06-09" — an archival snapshot, same
    category as `docs/handover_2026-08-18.md`; retroactively editing it would be
    wrong, not right), `docs/ux_principles_finanz_lern_apps.md` (names the 5
    benchmarked metrics specifically for the metric-school playground-porting
    exercise, a genuinely scoped claim about which metrics have that feature, not the
    general card-content claim this pattern is about), `docs/data_contract.md`'s
    `sector_median_*`/`sector_min_*`/`sector_max_*` column table (correctly describes
    the 5 *benchmarked* metrics specifically, unrelated to total displayed count),
    and a `tests/frontend/test_card_copy.py` code comment ("hero three," informally
    naming `importance_tier == 1`, a data concept that still exists — only the
    *visual* hero/tier split in card layout was removed, not the tier field itself).
  - `docs/data_contract.md` added to `scope_paths` this round mechanically triggers
    `equity-analyst-reviewer` per `.claude/review_routing.json` (already required via
    the catalogue CSV; no new reviewer type added).
  - **Round 5 review: scope-auditor FAILed a third consecutive round on the same
    "five metrics"/"hero" staleness class (equity-analyst-reviewer PASSed the one
    line in its own domain, `docs/data_contract.md`'s coverage-audit wording).** Two
    of the three findings were genuine misses in dbt-side files the round-4 "repo-
    wide" grep never actually covered (it was `docs/`-scoped in practice, despite the
    round-4 amendment's own claim to be repo-wide): `dbt_analytics/models/_docs.md`'s
    `{% docs card_metrics %}` block ("Five metrics power the stock swipe card...") and
    `dbt_analytics/seeds/_seeds.yml`'s `importance_tier` column description (still
    describing the removed visual hero/tier split). Both fixed. The third finding was
    a genuinely more sophisticated catch: `docs/product_roadmap_2026-06.md` had been
    blanket-exempted as archival in round 4's amendment, but the reviewer correctly
    distinguished that only its dated "Success criteria"/"Shipped" sections are
    actually archival — its "Verification checklist (each release)" section is a
    standing, repeatable procedure in the same category as `working_agreement.md`'s
    smoke-check (which *was* fixed round 4 for this exact claim), and contained the
    identical stale line. Fixed, same treatment. The reviewer's independent re-checks
    of round 4's other "left alone" calls (ux_principles, the benchmark-column table,
    `importance_tier`'s continued existence, the CRLF finding, the 2 quote fixes) all
    held up without needing further action.
  - **Genuinely repo-wide sweep, this time actually repo-wide** (previous rounds'
    "full sweeps" were `docs/`-scoped in practice, which is exactly how the round-5
    findings above slipped through). Found and fixed 5 more instances beyond the 3
    the reviewer named, across file types no earlier round had searched
    (**correction, scope-auditor round 6**: originally miscounted as "6" here — the
    diff substantiates 5, listed in full below; fixed the count rather than leave an
    inaccurate audit-trail claim standing, the same class of self-correction this
    task's process has required repeatedly)
    (`dbt_analytics/models/*.yml`, `README.md`, top-level `docs/*.md` not previously
    checked): `dbt_analytics/models/4_intermediate/_intermediate.yml`'s model
    description ("Five swipe-card metrics..."), `README.md` (both the architecture
    diagram's "Eligibility gate / five-metric data contract" node label and the
    Highlights section's "Five-metric eligibility contract" bullet — the most
    prominent, top-of-repo instance of this whole pattern, missed for 5 rounds),
    `docs/ui/discover_header.md` ("five-metric gate" in the About-the-data expander
    spec), `docs/metric_layer.md` ("`int_stock__card_metrics` computes the five
    metrics"). Independently re-verified (not just pattern-matched) several
    correctly-scoped "operating: the five-metric [set/AND/gate]" instances alongside
    explicit financial/pre_revenue siblings in `dbt_analytics/models/4_intermediate/
    _intermediate.yml:210`, `dbt_analytics/models/5_marts/_marts.yml:140`,
    `dbt_analytics/tests/assert_eligible_mart_rows_have_all_metrics.sql:2`,
    `dbt_analytics/models/4_intermediate/int_stock__card_metrics.sql:241`, and
    `dbt_analytics/models/_docs.md`'s `card_eligibility` block — all left alone,
    genuinely accurate (operating's eligibility gate really is still exactly 5
    metrics, correctly presented as one of three per-type rules, not a universal
    claim). `docs/backlog/discover_metric_filters_phase2.md` (a not-yet-built
    feature proposal for range-filtering "the five card metrics") checked and
    deliberately left alone: its 2 given examples (operating margin, forward P/E)
    are both benchmarked metrics, suggesting the proposal already means "the 5
    benchmarked metrics" specifically (the only ones with a natural min/max to range-
    filter on) rather than a stale general count — genuinely ambiguous without
    redesigning an unbuilt feature, which is out of scope here; flagged, not guessed
    at.
  - **Owner pulled the deferred onboarding-copy item back into scope directly**
    (`decisions_reserved`, above) — implemented 2 of the 3 owner-approved strings
    (`PRODUCT_TAGLINE`, the `landing.py` "How it works" bullet) plus, while touching
    `frontend/overflow_menu.py` for the third (`_SEARCH_TIP`, already owner-approved),
    found 2 MORE live strings in that same file with the identical stale claim that
    were never part of the original 3-string scope the owner approved:
    `MENU_METRICS_LINE` ("Five metrics per company — no substitutes," the "About the
    data" menu section) and `right_now_line()`'s Search-tab string ("Find any company
    with a complete five-metric snapshot"). Both fixed the same way (drop the false
    count, keep the sentence's rhythm), both em-dash-free. These 2 are a genuine,
    small scope extension beyond the specific 3 strings the owner literally approved
    — same class of metric-count product copy, found while directly implementing the
    approved work, not a separate unrelated decision; flagged here rather than
    silently folded in as if originally approved.
  - **Round 6 review: equity-analyst-reviewer and cto-reviewer PASSed (both thorough —
    cto-reviewer traced all 5 new/changed frontend strings to their real render call
    sites and cross-checked every CSV↔JSON field by hand); analytics-engineer-reviewer
    FAILed on a genuine misattribution in the builder's own round-5 fix.**
    `dbt_analytics/models/4_intermediate/_intermediate.yml`'s model-level description,
    "Swipe-card metrics (per company type) and eligibility per ticker snapshot,"
    grammatically attaches "(per company type)" to *metrics* — but
    `int_stock__card_metrics.sql`'s `metrics` CTE computes every metric identically
    regardless of `company_type`; only the separate `eligibility` CTE branches on it.
    Contradicts this same diff's own `docs/metric_layer.md` fix (also round 5:
    "computes every catalogued metric once," no per-type qualifier on the metrics
    themselves) and `docs/data_contract.md`'s canonical description (`company_type`
    computed "alongside the metrics," with per-type *metric sets* and *card display*
    both being downstream, non-model concerns). Fixed by moving the qualifier onto the
    thing that's actually per-type: "Swipe-card metrics and per-company-type
    eligibility per ticker snapshot." A precise catch — the underlying claim (this
    model has real per-company-type logic somewhere) was true, just misattached to the
    wrong half of the sentence.
  - **cto-reviewer's non-blocking observation, acted on anyway.** `MENU_METRICS_LINE`
    had zero test coverage before or after this task, despite being rewritten (twice,
    now, within this task alone) to fix the same recurring stale-metric-count class —
    exactly the kind of string the reviewer noted "would earn its keep" from a
    regression guard. Added `test_menu_metrics_line_has_no_stale_metric_count()`
    (`tests/frontend/test_overflow_menu.py`) — pins the exact current string and
    explicitly asserts no "five" and no em-dash, so a future revert or copy-paste from
    an older branch is caught by CI instead of needing another live-app spot-check.
