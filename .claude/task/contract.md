# Task contract

objective: Give the three percent-scale passthrough metrics a guard that actually guards.

  Yahoo returns `dividendYield` as a PERCENT (0.94 = 0.94%) but `returnOnEquity` and
  `revenueGrowth` as FRACTIONS. Three metrics pass an `info` scalar through with a fixed
  multiplier, so a provider units change ships a silent 100x error:
  `dividend_yield_pct` (no multiplier), `revenue_growth_yoy_pct` and `roe_pct` (both x100).

  `_intermediate.yml` claimed the dividend case was "caught by audit_mart_vs_yfinance, which
  now compares dividend_yield_pct as a mart metric". It was not: the field was in neither
  `METRIC_KEYS` nor `MART_COLUMNS`. Found by the pipeline audit (issue #9). The owner scoped
  dividendYield first, then asked for ROE and revenue growth in the same shape.

  Two structural reasons the audit script could never have been the guard, which is why the
  fix is a dbt test rather than an addition to it:
  1. It recomputes fresh yfinance through the same dbt code and diffs against the mart, so a
     flip shows as one run's drift then vanishes. It sees the transition, never the settled
     state.
  2. It never runs live: CI invokes it `--offline --sample-size 5`, and `--fail-on-drift` is
     never passed.

scope_paths:
  - dbt_analytics/tests/assert_percent_scale_passthroughs.sql
  - dbt_analytics/models/4_intermediate/_intermediate.yml
  - docs/data_contract.md
  - docs/metric_audit.md
  - scripts/seed_ci_raw_fixtures.py
  - scripts/audit_mart_vs_yfinance.py
  - tests/tooling/test_audit_mart_vs_yfinance.py
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/active_work.md

decisions_reserved:
  - Making `audit_mart_vs_yfinance.py` run live in CI (new recurring cost and a schedule
    change, §6). Not done. No comment may imply otherwise.
  - A coverage/fill-rate assertion. If a metric goes entirely null -- a provider dropping or
    renaming a field, likelier than a units change -- this guard passes having asserted
    nothing. That is a different assertion and the project has no `accepted_range` or
    fill-rate tests anywhere. Documented as a known hole, not built.
  - The sample floor has a REACHABLE silent-skip path. Reproduction, RUN rather than reasoned:
    null `info_dividend_yield` on two of the five generic operating fixtures. Dividend yield is
    not an eligibility field, so every market still reports 7 eligible and
    `check_eligibility_baseline.py` exits 0; meanwhile `populated_count` for
    `dividend_yield_pct` falls to 4, under the floor of 5, and this guard emits zero rows.
    Observed: `dbt build` 127/127 PASS with the dividend assertion silently disengaged. Today's
    margin is one fixture row. Closing it needs a floor assertion that FAILS rather than
    disengages, which is the coverage assertion reserved above.
    CORRECTION to an earlier draft of this entry, which claimed the same hole was reachable by
    REMOVING two dividend-paying fixtures. That is false: removing them drops eligible to 45
    against `total_baseline_eligible: 63`, breaching the 15% total floor of 53, so CI fails.
    I recorded a reviewer's reproduction verbatim without running it against
    `check_eligibility_baseline.py` -- the third time in this task that an unverified claim was
    adopted from a review finding.
  - The bands (0.5-50 / 1.0-100 / 1.0-200) and the sample floor (5) are data-integrity bounds
    derived from measurement, not user-visible metric definitions. Prior review judged this an
    implementation detail rather than §6; recorded in `docs/data_contract.md` so it is
    reviewable rather than buried.

done_when:
  - One test asserts scale ABSOLUTELY for all three metrics, not by comparison against the
    same provider through the same code.
  - Per market, so a single market ingesting post-flip is caught. A pooled median is a
    majority vote and would stay quiet until half the universe had flipped.
  - TWO-SIDED per metric, because the failure direction differs: a percent source can only
    break downward, a fraction source multiplied by 100 can only break upward.
  - MUTATION-VERIFIED per metric, per market, and in BOTH directions: 6 cases, 6 caught, each
    naming the offending market and metric. A guard nobody has watched fail is the defect being
    fixed, and round 1's mutation test passed while testing a direction that cannot occur for
    two of the three metrics.
  - The sample floor is proven to ENGAGE rather than silently skip, in CI fixture conditions.
  - The false claim in `_intermediate.yml` is corrected and points at a path that exists.
  - `dbt build`, `pytest tests/ -q`, `sqlfluff lint`, `check_dbt_sql_structure.py`,
    `check_dbt_tests.py` and `check_eligibility_baseline.py` all green locally before pushing.

impact_map: no value, column or formula changes anywhere; this change adds assertions and
  documentation only. No card face, verdict, or eligibility count moves. Correcting an earlier
  draft of this line, which implied only `revenue_growth_yoy_pct` reaches the mart:
    * `dividend_yield_pct` IS a mart column (`mart_stock_cards.sql:33`) and IS exported
      (`export_to_supabase.py:52`). It is data-only in the sense that no card renders it: no
      catalogue row, absent from `frontend/metrics.json`, not an eligibility field.
    * `revenue_growth_yoy_pct` is a mart column AND an operating eligibility field.
    * `roe_pct` is neither: it exists only in `int_stock__card_metrics`.

  The audit script gains one compared metric, widening its DuckDB/Supabase reads AND its
  optional `--fail-on-drift` gate. That gate applies one relative 25% threshold to every
  metric, and Yahoo quantises `dividendYield` to 2dp, so on a pilot ticker with a ~0.02 yield
  (NVDA is in `DEFAULT_ALWAYS`) a single rounding tick reads as 33-50% drift. CI never reaches
  it: `--fail-on-drift` requires `not args.offline` and CI passes `--offline`. A manual-command
  annoyance, recorded rather than fixed.

  ONE PRODUCTION-DATA VALUE CHANGES, in CI fixtures only: `seed_ci_raw_fixtures.py`'s
  `info_dividend_yield` goes 0.02 -> 2.0 on the five generic operating fixtures. This is
  LOAD-BEARING for the new guard passing CI -- at 0.02 the per-market median is 0.02, below the
  0.5 floor, and the test fails. It is legitimate only because the fixture was independently
  wrong: 0.02 under Yahoo's percent contract means a 0.02% yield, it sat beside
  `info_payout_ratio: 0.30` (a field that genuinely IS a fraction), and the sibling
  `_bank_fundamentals` already used 3.5 with a docstring saying "a percent dividend yield".
  cto-reviewer dated both fixtures either side of the percent discovery. Stated here rather
  than left for a reviewer to find.

amendments:
  - SUPERSEDED the first implementation. Round 1 shipped
    `assert_dividend_yield_is_percent_scale.sql`, a pooled signed median over the MART for one
    metric. analytics-engineer-reviewer and scope-auditor both returned FAIL; cto-reviewer
    PASSed with two non-blocking findings. Every finding is addressed by the redesign rather
    than patched:
      * `paying_count > 0` was a provable no-op (median of an empty set is NULL, and
        `NULL < 0.5` filters out anyway) AND made the test fail on correct data -- a single
        legitimate row at 0.0036 tripped it, which would block the export. Replaced with a real
        floor of 5, verified to engage across all 9 markets x 3 metrics in CI.
      * A pooled median is a majority vote; one market flipping (~1/9 of payers) never trips it.
        Now grouped by `market_code`.
      * A signed median understates scale for `revenue_growth_yoy_pct` and `roe_pct`, which are
        14% and 10% negative. Now the median of the ABSOLUTE value.
      * A 5-line comment block violated §1.2 "No multi-line comment blocks". Round 2 correctly
        rejected "now 3 lines" as still a block, and caught a 4-line replacement in
        `_intermediate.yml` breaking the same rule in the change that claimed to honour it.
        Both are now ONE line each, with all provenance in `docs/data_contract.md`.
      * "measured live 2026-09-08" was a date stamp inside SQL, which the repo forbids. Removed.
      * The comment pointed at `tests/...`, ambiguous against the repo's top-level pytest
        `tests/`. Now `dbt_analytics/tests/...`.
      * Moved from the mart to `int_stock__card_metrics`: `docs/layering.md` assigns "expected
        ranges" to `4_intermediate`, the sample is all tickers rather than eligible-only, and it
        is the only place `roe_pct` exists at all.
  - Added `docs/data_contract.md` to scope_paths. The test comment cites it for thresholds and
    provenance; writing the pointer without the section would reproduce the dead-pointer defect
    the audit filed against four existing SQL comments.
  - Added `tests/tooling/test_audit_mart_vs_yfinance.py`: `_make_mart_duckdb` derives its DDL
    from `MART_COLUMNS` but inserts hardcoded positional tuples, so adding a column broke it.
    One value added per row. Direct fallout, not widening.
  - `roe_pct` exposure is smaller than the audit implied and this is stated rather than glossed:
    it is data-only and reaches no consumer, and the ROE users actually see
    (`statement_roe_pct`) is computed from statement line items, so it carries no provider-scale
    exposure of this kind. `roe_pct` is guarded anyway so promoting it later cannot silently
    ship an unguarded passthrough. Its floor could NOT be measured from production (not
    exported); `statement_roe_pct`'s median |value| of 13.37 is the stated proxy.
  - Measured evidence for the bands (live production, latest snapshot, exported mart only --
    see the population caveat below): per-market dividend medians run 1.81 (`us_sp500`) to 3.53
    (`au_asx200`); revenue-growth median absolute value runs 4.50 (`fr_cac40`) to 12.00
    (`jp_nikkei225`). CORRECTION to an earlier draft of this line, which said "a flip divides
    each by 100": that is true ONLY for `dividend_yield_pct`. The other two arrive as fractions
    and are multiplied by 100 in the model, so a flip MULTIPLIES their median by 100.
  - ROUND 2 found a design error that invalidated the guard for two of its three metrics, and
    it is the most important correction in this task. The test was a LOWER bound only. That is
    right for `dividend_yield_pct` (Yahoo returns percent, model passes through, so a flip makes
    values 100x SMALLER), but `revenue_growth_yoy_pct` and `roe_pct` arrive as FRACTIONS and the
    model applies x100, so their flip makes values 100x LARGER and moves the median AWAY from a
    floor. analytics-engineer-reviewer mutation-proved it: multiplying one market by 100
    produced zero failing rows for both. My own round-1 mutation test divided by 100 for all
    three, validating a mutation that cannot occur for two of them -- it looked rigorous and
    tested the wrong direction. Now a two-sided band per metric, mutation-verified in BOTH
    directions for all three (6 cases, 6 caught).
  - Round 2 also caught the margin evidence being measured on the wrong population: the figures
    come from the exported mart (eligible-only) while the test reads `int_stock__card_metrics`
    (all tickers). `docs/data_contract.md` now states this explicitly rather than implying the
    numbers describe the tested population.
  - The broken markdown table in `docs/data_contract.md` (unescaped pipes in `Min median |value|`
    gave 7 header cells against a 5-cell delimiter, so the table the SQL comment cites did not
    render) is fixed by rewording the headers.
  - NEW FINDING, filed as issue #10, not fixed here: production currently holds `dividendYield`
    in MIXED units. AvalonBay (0.0387) and Equity Residential (0.0426) are residential REITs
    yielding ~4%; those rows are fraction-scale in a percent-scale column. This falsifies the
    repo's recorded "yfinance dividendYield is a PERCENT" as a universal, and it also weakens
    this task's own argument that no per-row range is possible -- that rested on 0.0036 being a
    legitimate minimum, and it probably is not a real value at all. A per-market median guard
    structurally cannot see per-row mixed units, so this is genuinely out of its scope, but the
    limitation is now documented rather than implied.
  - Round 3: analytics-engineer-reviewer PASSed, having independently re-run all 6 mutation
    cases against the compiled SQL rather than accepting mine. scope-auditor FAILed on two
    prose defects, both fixed:
      * The docs reported a `roe_pct` flip landing at 2372 while the same row said the value
        was "not measurable" and the stated proxy was 13.37. Two different numbers were being
        mixed: 13.37 is the POOLED median of `statement_roe_pct`, 23.72 is its highest
        PER-MARKET median. The band is derived from the per-market range, since the test groups
        by market, so both figures and their populations are now stated.
      * "20 dividend payers (`ch_smi`)" did not state its population, inside the paragraph set
        added specifically to disclose populations. Now says: exported mart, latest snapshot,
        20 eligible rows all carrying a dividend.
  - Three non-blocking round-3 observations, all acted on rather than filed:
      * The "under a flip" column mixed extremes -- lowest market for dividend, highest for the
        other two -- making the revenue-growth margin look 2.7x better than the binding case.
        Now states the binding case for each, with the rule spelled out.
      * The population caveat did not say which way the superset skews. An answer was added
        here claiming a ceiling-ward skew via pre-revenue exclusion. THAT ANSWER WAS FALSE; see
        the round 5 entry below.
      * `docs/metric_audit.md`'s decision log enumerated five metrics against what is now a
        six-metric comparison set. Added `docs/metric_audit.md` to scope_paths and added the
        row, noting the real guard is the dbt test rather than this script.
  - Round 4, scope-auditor FAIL, three findings, all in the prose added in round 3 to fix
    round 3's prose. Worth recording as a pattern, not just a fix:
      * The dividend row's binding case was WRONG, and arithmetically so. For a percent source
        breaking downward against a FLOOR, dividing by 100 leaves the HIGHEST market nearest the
        floor (`au_asx200` 3.53 -> 0.035, 14x clear), not the lowest (`us_sp500` 1.81 -> 0.018,
        28x). I moved the two fraction rows to their binding market correctly and left dividend
        at the loose extreme -- the same overstatement round 3 flagged, reintroduced on a
        different row while claiming to have fixed it.
      * The selection rule I wrote to justify that table said "the lowest market for a percent
        source ... the lowest for a fraction source": the same instruction twice, presented as a
        contrast. The directions are opposites. Rewritten with both cases and their arithmetic.
      * The population-skew claim was asserted for all three metrics on a mechanism that
        supported at most one. Narrowed to `revenue_growth_yoy_pct` -- which round 5 then
        showed was the wrong metric to keep it for, because the mechanism is false outright.
  - Round 5, scope-auditor FAIL: the population-skew claim was FALSE, not merely over-broad,
    and it is worth recording how it got in. It originated as an observation from
    analytics-engineer-reviewer in round 3 ("pre-revenue names, explicitly excluded from the
    mart, are exactly the extreme-growth population"). I adopted it without checking, then
    defended and narrowed it across two further rounds. Verified directly this round, it fails
    three ways:
      * `mart_stock_cards.sql:99`'s `and m.company_type != 'pre_revenue'` is a condition on the
        LEFT JOIN to sector benchmarks, not a row filter. Pre-revenue rows are in the mart.
      * Pre-revenue has its own eligibility branch, `net_cash is not null`
        (`int_stock__card_metrics.sql:325-327`), so it is card-eligible by design.
      * Only 3 pre-revenue companies exist app-wide (`docs/data_contract.md`), which cannot
        move a per-market median.
    The claim is now deleted rather than re-narrowed: the honest statement is that the
    direction of the eligible-vs-superset difference is not established, because the ineligible
    population is exactly what the export leaves behind and nothing measures it.
    LESSON, recorded because it caused four rounds of churn: a reviewer's observation is not
    evidence. This one was adopted verbatim into documentation without being traced to source.
  - Round 6, scope-auditor FAIL, and the finding was inside the paragraph recording round 5's
    lesson, which makes it the clearest possible illustration of that lesson. I wrote that
    pre-revenue rows "carry NO revenue growth to skew with (`stmt_total_revenue <= 0` leaves it
    null)", under a heading claiming I had verified it directly. It is false.
    `revenue_growth_yoy_pct` is defined once, at `int_stock__card_metrics.sql:123`, as
    `s.info_revenue_growth * 100.0`; it is null only when Yahoo's scalar is null. The
    `stmt_total_revenue <= 0` test at `:259-261` sets the `company_type` LABEL and touches no
    metric value. I verified two of that entry's three bullets by grep and copied the third from
    the reviewer's own finding without checking it -- the exact failure the entry was written to
    record. The false clause is removed and its bullet now carries only the pre-revenue count;
    whether Yahoo returns a growth figure for pre-revenue tickers is unmeasured, so nothing is
    claimed about it.
  - Also round 6, non-blocking but the same reflex: `docs/data_contract.md` said the
    eligible-subset margins "are indicative of" the tested population one sentence after saying
    the direction of the difference is not established. "Indicative" asserts a
    representativeness nothing here measures. Reworded to state only what was measured.
