# Task contract

objective: Outlier-aware metric-range scaling (Gemini feedback point 5,
  `docs/backlog/gemini_verdict_feedback.md`). `frontend/card_copy.py`'s `benchmark_range()` scales
  a card's marker linearly across its sector's raw min/max; one extreme peer (documented today in
  `docs/ui/card_metric_cell.md`'s "Known data-quality interaction" note -- Deep Yellow/DYL,
  -129,810.5% FCF margin, ASX Energy) dominates the whole sector's axis, compressing every OTHER
  card's marker toward one end regardless of how ordinary that card's own number actually is. Owner
  confirmed the direction after reviewing a mockup: clamp the DISPLAYED range using a Tukey fence
  (`Q1 - 1.5*IQR` to `Q3 + 1.5*IQR`, the standard box-plot convention for outlier bounds, not an
  invented multiplier), pin an off-scale marker to the clamped edge with a small directional arrow,
  and keep showing the card's own true raw value as plain text (unchanged, in the value row above
  the bar) regardless of where the marker sits. Log-scaling was explicitly rejected (not beginner
  friendly -- this app's whole design stance is plain-language, no naive/misleading visual tricks).

  This needs new backend data the mart does not carry today: quartiles (Q1/Q3) per benchmarked
  metric, alongside the existing min/median/max. That makes this a dbt + Supabase export change,
  not a pure frontend tweak as `docs/backlog/gemini_verdict_feedback.md`'s candidate direction 5
  currently frames it -- flagged to the owner before scoping, this contract corrects that framing.

  Only 4 metrics are actually benchmarkable today (verified against `metric_catalogue.csv`):
  `ebit_margin_pct`, `revenue_growth_yoy_pct`, `net_debt_to_ebitda`, `fcf_margin_pct`. `forward_pe`
  carries dead, unused min/median/max columns already (it left the catalogue) -- do NOT add
  quartile columns for it.

scope_paths:
  - dbt_analytics/models/4_intermediate/int_stock__sector_benchmarks.sql
  - dbt_analytics/models/4_intermediate/_intermediate.yml
  - dbt_analytics/models/5_marts/mart_stock_cards.sql
  - dbt_analytics/models/5_marts/_marts.yml
  - supabase/migrations/*.sql (one new migration file)
  - scripts/export_to_supabase.py
  - frontend/card_copy.py
  - frontend/card_ui.py
  - frontend/styles.py
  - tests/tooling/test_*.py (dbt-adjacent Python tests, if any touch these columns)
  - tests/frontend/test_card_ui.py
  - tests/frontend/test_card_copy.py
  - docs/data_contract.md
  - docs/ui/card_metric_cell.md
  - docs/backlog/gemini_verdict_feedback.md
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/active_work.md

decisions_reserved:
  - **Whether the words row still says "min"/"max"** once those positions represent a
    fence-clamped display bound rather than the literal most-extreme peer in the sector. The
    numbers row's min/max VALUES change (they become the fence bound, not the raw sector
    extreme, whenever a real outlier exists); the words underneath currently just say "min" and
    "max". Keeping that wording could read as a claim about the actual peer-group minimum/maximum
    when it is not one. Two honest options, not decided here: (a) keep "min"/"max" as-is --
    defensible since they still literally are the low/high edge of what is DISPLAYED, the same
    sense a chart axis's own min/max already means; (b) reword to something that doesn't imply
    "the worst/best peer" (e.g. "low"/"high"). This is user-visible wording (§6).
  - **Whether the off-scale arrow needs any label/tooltip** beyond the bare glyph (e.g. hover
    text like "actual value shown above" or a `title` attribute), or whether the raw value already
    sitting in the value row above the bar is enough context on its own, matching this app's
    existing minimal, no-tooltip style elsewhere on the card face.
  - **Exact glyph/styling for the off-scale indicator** -- the mockup used a plain ◂/▸ character;
    not confirmed as final art direction.

done_when:
  - `dbt_analytics/models/4_intermediate/int_stock__sector_benchmarks.sql`: for each of the 4
    benchmarkable metrics, two new aggregate columns `sector_q1_<metric>` /
    `sector_q3_<metric>` using `quantile_cont(<metric>, 0.25)` / `quantile_cont(<metric>, 0.75)`
    (DuckDB's continuous-quantile function, the same interpolation family `median()` already
    uses), gated through the identical `sector_peer_count >= 8` CASE-null pattern the existing
    min/median/max columns use -- same threshold, no new number invented. `forward_pe` gets NO
    new quartile columns.
  - `dbt_analytics/models/4_intermediate/_intermediate.yml`: column descriptions added for the 8
    new columns (4 metrics x Q1/Q3), matching the existing description style/verbosity for their
    sibling min/max columns. The existing `sector_benchmarks_min_le_median_le_max` expression
    test extended (or a sibling test added) to assert `min <= q1 <= median <= q3 <= max` for the
    4 metrics that now have quartiles; `forward_pe`'s existing `min <= median <= max` clause is
    untouched. The existing null-together `dbt_utils.expression_is_true` test's expression
    extended to include the 8 new columns in the same all-null-together clause. The existing
    `sector_medians_populated_when_eight_eligible_peers` unit test (or a new sibling unit test)
    extended with a concrete given/expect fixture that proves a specific quartile value from
    specific input rows -- pin to literal numbers computed by hand, not derived from the same
    formula being tested (`docs/ui/card_metric_cell.md`'s own anti-pattern list already warns
    against this for range-mark fixtures).
  - `dbt_analytics/models/5_marts/mart_stock_cards.sql`: the 8 new columns selected through from
    `int_stock__sector_benchmarks`, same pattern as the existing min/median/max pass-through.
  - `dbt_analytics/models/5_marts/_marts.yml`: matching column descriptions added at the mart
    layer (mirrors the intermediate layer's descriptions, per this repo's existing convention for
    sibling min/max columns).
  - `supabase/migrations/`: one new migration file (following `012_sector_benchmark_min_max.sql`'s
    exact pattern -- `alter table ... add column if not exists ... numeric`) adding the 8 new
    `sector_q1_*` / `sector_q3_*` columns to the mart table Postgres side.
  - `scripts/export_to_supabase.py`: the 8 new column names added to the export column list
    (mirrors where `sector_min_*`/`sector_max_*` already are).
  - `frontend/card_copy.py`: `benchmark_range()` rewritten to compute the display range as a
    Tukey fence (`max(sector_min, q1 - 1.5*iqr)` .. `min(sector_max, q3 + 1.5*iqr)`, using the
    STANDARD 1.5 multiplier, not a value picked to fit any one card) instead of raw
    `[sector_min, sector_max]`, when q1/q3 are present; falls back to the current raw-min/max
    behavior when q1/q3 are null (a sector that qualified before this ships, or any transitional
    state) so nothing regresses to "no mark" during rollout. Returns whether the company's own
    value fell outside the clamped range on either side (for the off-scale arrow), alongside the
    existing `min`/`median`/`max`/`value`/`position_pct`/`median_pct` keys -- `min`/`max` in the
    returned dict become the CLAMPED bound (what's actually shown at 0%/100%), not the raw sector
    extreme, so `_metric_range_html()` needs no separate "which number do I print" branch.
  - `frontend/card_ui.py`: `_metric_range_html()` renders the off-scale arrow (direction depends
    on which side clamped) when `benchmark_range()` reports the value fell outside the clamped
    range; renders nothing extra otherwise. The card's own raw value in `.ss-metric-value` is
    completely unaffected by any of this -- verify by inspection, not just by test, that no path
    in this change touches `_metric_cell_html()`'s value row.
  - `frontend/styles.py`: new CSS for the off-scale arrow, styled as a small, clearly secondary
    glyph (not competing with the marker itself for attention).
  - Tests: `benchmark_range()` covered for (a) a normal case unchanged in behavior when no value
    falls outside the fence (existing tests must still pass), (b) a fence narrower than the raw
    min/max due to a real outlier peer, pinned to literal hand-computed numbers, (c) a peer whose
    OWN value is the outlier -- clamped position + off-scale flag set, (d) the null-q1/q3
    fallback path. `_metric_range_html()`/`_metric_cell_html()` covered for the off-scale arrow
    rendering and for confirming the raw value display is unchanged in the outlier case.
  - `docs/data_contract.md`: 8 new column rows added to both places `sector_min_*`/`sector_max_*`
    already appear (the intermediate-layer summary table and the exported-schema table).
  - `docs/ui/card_metric_cell.md`: "Range mark mechanics" section updated to describe the fence
    clamp and the off-scale arrow; the existing "Known data-quality interaction" note (which
    names this exact DYL/ASX-Energy case as unresolved) updated to reflect that it is now
    addressed, with a pointer to this branch; 480px smoke checklist gets one new line for the
    off-scale arrow not clipping or colliding at narrow width.
  - `docs/backlog/gemini_verdict_feedback.md`: point 5 marked acted on, with a pointer to this
    branch; candidate direction 5 corrected to note the actual scope (dbt + Supabase export
    change, not "purely a display change" as originally framed).
  - `pytest` and `dbt build`/`dbt test` (or the CI-equivalent local commands this repo uses) both
    green. No verdict-computation change anywhere -- `scripts/assessment_rules.py` untouched.
  - No em dash or en dash on any added line.

impact_map:
  - Every card face showing a benchmarked metric's range mark (4 metrics, any sector with
    `sector_peer_count >= 8`) changes its axis bounds whenever that sector has a real outlier
    peer -- the visual position of EVERY peer's marker in that sector can shift, even though no
    underlying metric value changes. This is a display-only change: `health_verdict` and `ai_read`
    are completely untouched, traced via `scripts/assessment_rules.py` (not in scope_paths, not
    read by anything this task touches).
  - New dbt aggregate columns are computed from the SAME `int_stock__card_metrics` eligible-peer
    rows already feeding `sector_median_*`/`sector_min_*`/`sector_max_*` -- no new upstream
    dependency, no new ingestion field. Negligible incremental runtime: 8 more aggregate
    expressions in an already-existing `GROUP BY market_code, sector` (same cost class as the
    `median()` calls already there), not a new join or a per-row computation.
  - Requires a new Supabase migration (schema change) and an `export_to_supabase.py` column-list
    update -- both additive (new nullable columns), no existing column type or semantics changed,
    no backfill needed (existing rows get the new columns as null until the next scheduled
    pipeline run recomputes them).
  - This touches Streamlit rendering (`frontend/card_ui.py`, `frontend/card_copy.py`,
    `frontend/styles.py`), so `docs/working_agreement.md`'s UX PR gate applies: north_star check
    (no north_star.md rule contradicted -- range marks are Tier 2, unaffected by this at that
    level of description), component-spec check (`docs/ui/card_metric_cell.md` updated in this
    same task, since it is the current source of truth for this exact element and already
    documents the problem being fixed), one primary job + mobile wireframe in the MR body, 480px
    smoke test before commit.
  - Corrects `docs/backlog/gemini_verdict_feedback.md`'s candidate direction 5, which described
    this as "purely a display change; doesn't touch verdict computation" -- the verdict-computation
    half of that claim still holds, but "purely a display change" undersells it: this is a real
    dbt-layer + Supabase-schema change, traced above, not a frontend-only edit.

amendments:
  - Owner said "go ahead on the implementation" without answering the three
    `decisions_reserved` questions. None of the three block the mechanism, so implementation
    proceeds using the safest, non-committal default for each, explicitly NOT as a final answer:
    (1) the words row keeps saying "min"/"max" unchanged -- no rewording attempted; (2) the
    off-scale arrow ships with no tooltip, matching this app's existing minimal style elsewhere;
    (3) the mockup's ◂/▸ glyph ships as-is. All three stay open and revisitable; none are treated
    as owner-decided by this amendment.
