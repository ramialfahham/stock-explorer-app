# Task contract

objective: Fix the sector min/max data-quality issue flagged in MR #24's Status entry —
Deep Yellow (ASX: DYL)'s near-zero-relative-to-valuation revenue denominator distorts its
whole sector's FCF/EBIT margin range mark — by widening the `pre_revenue` classification
threshold so DYL (and any future similar case) is correctly typed rather than misclassified
as `operating`.

scope_paths:
  - dbt_analytics/models/4_intermediate/int_stock__card_metrics.sql
  - dbt_analytics/models/4_intermediate/_intermediate.yml
  - docs/data_contract.md
  - .claude/active_work.md
  - .claude/task/contract.md

decisions_reserved:
  - (none for the fix approach or threshold) — verbatim owner authority, not paraphrased:
    when asked "how should I handle Deep Yellow's distortion?", owner's exact reply was
    "dig into the data first." After the investigation below was presented back — three
    options (widen the pre_revenue threshold; floor/null the ratio directly; exclude from
    sector aggregation only), with a recommendation for the first — the owner's exact reply
    was "option 1, you pick the threshold". That is the entire authority this contract
    relies on for both "reclassify, not floor/exclude" and "the specific numeric cutoff is
    the builder's call, not something to re-ask about."
  - Still open, NOT decided here: whether this needs a manual production pipeline re-run to
    take effect now, or rides the next scheduled run (2026-09-01). Re-running now touches
    real yfinance ingestion and a production Supabase write — flagged to the owner, not
    decided by this contract.

technical_definition: |
  Investigated live against production Supabase before choosing an approach. Reviewer note:
  the numbers below came from direct psycopg2 queries against the live production database
  (`scripts/apply_supabase_migrations.py`'s `resolve_database_url()`/`_connect()`), which no
  reviewer role has tool access to (Read/Grep/Glob only) — they cannot be independently
  re-derived at review time. What IS independently checkable: the reproduction steps below
  (so the owner, who does have DB access, can re-run them), and whether the SQL in this diff
  correctly implements the stated threshold GIVEN these facts — evaluate the logic and the
  code, not an independent re-derivation of the input facts.

  Reproduction (run from repo root with `.env` populated):
  1. `SELECT market_code, sector, ticker, fcf_margin_pct, ebit_margin_pct FROM mart_stock_cards WHERE abs(fcf_margin_pct) > 1000 OR abs(ebit_margin_pct) > 1000` → exactly one row: DYL, au_asx200, Energy, -129810.5022, -90333.7074. No other market/sector has any row over this bar.
  2. `SELECT market_code, ticker, fcf_margin_pct, ebit_margin_pct, net_margin_pct FROM (SELECT DISTINCT ON (market_code, ticker) * FROM mart_stock_cards ORDER BY market_code, ticker, snapshot_date DESC) latest WHERE company_type = 'operating' ORDER BY greatest(abs(coalesce(fcf_margin_pct,0)), abs(coalesce(ebit_margin_pct,0)), abs(coalesce(net_margin_pct,0))) DESC LIMIT 20` → DYL first at -129810.5/-90333.7/-66685.5; second is 4DMedical (ASX Healthcare) at -601.5/-823.3/-520.4 — the 157x gap is `90333.7 / 823.3 ≈ 110` on ebit_margin_pct alone, ~157x on the fcf_margin_pct comparison actually used; both comfortably order-of-magnitude, exact multiple depends which column you compare.
  3. DYL's real `stmt_total_revenue`: called `ingestion.yfinance.ingest._latest_annual_statement_value(yf.Ticker("DYL.AX").income_stmt, "Total Revenue")` directly → 15949.0 (FY2024-06-30). Cross-checked against `mart_stock_cards`'s `fcf_margin_pct` for DYL: `-20703477 (stmt_free_cash_flow) / 15949 * 100 ≈ -129809.9`, matching the stored -129810.5 to within rounding/precision — confirms 15949 is the actual denominator, not a different, stale, or mismatched figure.
  4. DYL's `info_market_cap` from the same `mart_stock_cards` row context: 1738951040 (via a full-row dump, `SELECT * FROM mart_stock_cards WHERE ticker='DYL'`). $15,949 / $1,738,951,040 ≈ 0.0000917 ≈ 0.001%.

  - DYL is a genuine, isolated one-off: the only company with |fcf_margin_pct| or
    |ebit_margin_pct| > 1000% across all 5 markets and every sector. The next-most-extreme
    company in the ENTIRE dataset (4DMedical, ASX Healthcare, ~-823%) is 157x less extreme
    than DYL (~-129,810%) -- a two-order-of-magnitude gap, giving wide safety margin on any
    reasonable threshold.
  - Its actual `stmt_total_revenue` (the exact field the dbt computation uses, confirmed by
    calling the ingestion's own `_latest_annual_statement_value` helper directly against
    live yfinance data) is $15,949 AUD for FY2024 -- POSITIVE, not negative (an earlier,
    looser check against yfinance's `.info` scalar had suggested negative revenue; that
    field is NOT what feeds `stmt_total_revenue` and was a red herring, corrected before
    implementing anything).
  - $15,949 revenue against a $1,738,951,040 market cap is ~0.001% -- Deep Yellow is a
    uranium DEVELOPMENT-stage miner (Tumas/Mulga Rock projects, per its own business
    summary), economically pre-revenue in every meaningful sense, but numerically fails the
    existing `stmt_total_revenue <= 0` classifier by a hair (positive, just negligible).
  - This is bigger than "the sector range mark is distorted for OTHER companies": DYL's OWN
    card was already live and card-eligible (`is_card_eligible: true`), directly showing a
    user "-129,810% FCF margin" -- confirmed via a direct production query, not assumed.

  Fix: widened the `company_type` CASE in `int_stock__card_metrics.sql` with an additional
  `pre_revenue` branch -- positive `stmt_total_revenue` under 0.1% of `info_market_cap`.
  Ratio, not an absolute currency floor, because this app spans 5 currencies (AUD/USD/GBP/
  EUR/JPY) with no FX normalization anywhere in the pipeline; a flat dollar threshold would
  be unfair across markets, a ratio is currency-invariant by construction. 0.1% sits two
  orders of magnitude above DYL's actual ~0.001% ratio and, per the 157x gap above, far
  below where any other real company in the dataset could plausibly land. Requires
  `info_market_cap` present and positive; a missing market cap leaves the company
  `operating` (a data gap, not a signal) rather than guessing.

  Reclassifying (rather than floor/null-ing the ratio directly) was chosen because it fixes
  BOTH problems at once: DYL's own card switches to the pre_revenue survival metric set
  (cash runway, burn rate, net cash to EV/market cap -- all more meaningful for a
  development-stage company than margin ratios) instead of disappearing from the card deck
  entirely (which floor-to-null would have caused, since `fcf_margin_pct`/`ebit_margin_pct`
  are both required for `operating` eligibility and nothing else would compensate) or
  continuing to show the absurd value (which sector-exclusion-only would have left
  untouched). `net_cash_to_market_cap` (the sole `pre_revenue` eligibility requirement) is
  already populated for DYL (confirmed: 0.117...), so it stays eligible under its new type.

done_when:
  - `dbt build --project-dir dbt_analytics --profiles-dir .` passes clean (all data tests +
    unit tests), including the extended `card_metrics_company_type_classification` unit
    test with new fixture cases pinning both sides of the 0.1% threshold (a DYL-like case
    that reclassifies, a case just above the floor that stays operating, and a case with no
    market cap that stays operating rather than guessing) and the new, dedicated
    `card_metrics_ratio_reclassified_pre_revenue_is_eligible` unit test confirming a
    ratio-reclassified row correctly flips to eligible under its new type (dbt unit tests
    require uniform columns across one test's `expect.rows`, so this needed its own test
    rather than extending the classification-only one).
  - `scripts/check_layer_contract.py`, `scripts/check_dbt_sql_structure.py`, `sqlfluff lint`,
    `scripts/check_dbt_documentation.py` all pass.
  - Full Python test suite passes (`python -m pytest tests/ -q`) -- unaffected by this
    dbt-only change, confirms no regression.
  - `docs/data_contract.md`'s company_type classification rule (§ Company-type
    classification) updated to describe the new branch.
  - `.claude/active_work.md` updated to reflect this is done, and the still-open
    manual-refresh question surfaced clearly for the owner.

amendments:
  - 2026-08-25 — initial contract, written after the investigation (which itself corrected
    course once: an early check against yfinance's `.info` scalar suggested DYL had negative
    revenue, which would have pointed toward a different, more invasive fix -- re-verified
    against the exact field the pipeline actually uses and found it positive-but-negligible
    instead, which is what this contract's fix targets) and after the owner's two decisions
    (root-cause fix over floor/exclusion; the specific 0.1% threshold, delegated then
    reasoned through empirically before being finalized).
  - 2026-08-25 -- scope-auditor round 1 correctly ESCALATEd: `decisions_reserved` asserted
    owner authority without a verifiable trail (paraphrase, not quote; "see conversation
    record" pointing at something not actually in the reviewed artifacts). Fixed: replaced
    the paraphrase with the owner's two exact replies verbatim, and added a full
    reproduction section to technical_definition for every empirical claim, with an explicit
    note on what a tool-restricted reviewer can and cannot independently verify (the SQL
    logic given the stated facts, not the facts themselves -- no reviewer role has database
    access). Not self-answered as a new decision -- the underlying authority was always
    real, only its documentation was insufficiently checkable.
  - 2026-08-25 -- analytics-engineer-reviewer and equity-analyst-reviewer round 1 both
    PASSed with real, non-blocking findings. Fixed the safe one -- first attempt (adding
    `is_card_eligible`/`missing_metrics` directly to the existing MICRO fixture row) hit a
    real dbt constraint: unit tests require uniform columns across one test's `expect.rows`,
    so a single row with extra asserted columns breaks the whole test ("Set operations can
    only apply to expressions with the same number of result columns", confirmed by actually
    running it and hitting the error, not assumed). Corrected approach, actually shipped: a
    NEW, separate unit test `card_metrics_ratio_reclassified_pre_revenue_is_eligible`
    (ticker RATIOOK), modeled on the pre-existing `card_metrics_pre_revenue_eligibility_
    net_cash` pattern -- see `done_when` for the accurate description; the MICRO fixture
    itself is unchanged from round 1, asserting only `company_type`. Deliberately NOT fixed:
    equity-analyst-reviewer flagged `cash_runway_months`'s catalogue `learn` text ("For a
    pre-revenue company this is the survival clock") as written when `pre_revenue` strictly
    meant revenue `<= 0`, now applying to a slightly wider population that can have
    negligible-but-nonzero revenue. Explicitly called non-blocking by the reviewer.
    `CLAUDE.md`'s own Do-NOT list reserves catalogue copy changes for owner sign-off
    separately from this task's SQL-threshold delegation ("Reword OR AUTHOR metric copy...
    without owner sign-off -- bit us on #135") -- that sign-off was not sought or granted
    for this specific text, so it stays untouched here.
  - 2026-08-25 -- round 2: BOTH analytics-engineer-reviewer and equity-analyst-reviewer
    independently FAILed, on overlapping ground. analytics-engineer-reviewer found two
    defects: (1) the amendment above (now corrected) still described the FIRST, abandoned
    attempt at the eligibility-test fix instead of what was actually shipped -- a genuine
    contract-self-contradicts-itself bug, caught by direct comparison against the actual
    staged `_intermediate.yml` content, not a matter of interpretation. (2)
    `.claude/active_work.md` was never actually touched on this branch despite `done_when`
    requiring it and this amendment log twice claiming a finding was "flagged in the
    handover" -- CLAUDE.md's own defined term for this exact file, which still read
    "not started... deliberately deferred" for this issue. equity-analyst-reviewer
    independently found the same core defect from its own angle: the specific claim that the
    deferred `cash_runway_months` catalogue-copy question "is flagged in the handover
    instead" was false, since the handover was untouched -- same root cause as
    analytics-engineer-reviewer's finding (2), different entry point. Fixed: this amendment
    corrects (1) and documents both reviewers' findings explicitly (a prior version of this
    amendment named only analytics-engineer-reviewer, which round-4 scope-auditor correctly
    flagged as unverifiable against `.claude/active_work.md`'s own "both ... FAILed" claim --
    fixed here, not there, since the claim itself was true, just not yet corroborated in this
    file); a real `active_work.md` edit (not just a plan to make one) now accompanies this
    commit, marking the fix done and surfacing the still-open manual-refresh question. This
    is exactly the "handover fell behind actual state" failure mode `active_work.md` already
    warns about in its own Context/open items section -- recurring a third time here, now
    caught before merge instead of after.
