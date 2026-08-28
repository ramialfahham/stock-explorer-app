# Task contract

objective: Fix eleven wrong company names on live `jp_nikkei225` cards by building the
  seed-to-staging-to-base name-override mechanism the owner decided on 2026-08-28, and
  populating it with the eleven Nikkei corrections. Does not touch the raw seed CSVs, does not
  cover the Block ticker, does not cover the SMI legal-name register (separate, larger, needs
  its own trade-name research).

scope_paths:
  - dbt_analytics/seeds/company_name_overrides.csv
  - dbt_analytics/seeds/_seeds.yml
  - dbt_analytics/models/1_staging/manual/stg_manual__company_name_overrides.sql
  - dbt_analytics/models/1_staging/manual/_manual_staging.yml
  - dbt_analytics/models/2_base/yfinance/base_yf__constituents.sql
  - dbt_analytics/models/2_base/yfinance/_yfinance_base.yml
  - dbt_analytics/models/2_base/yfinance/_yfinance_base_unit_tests.yml
  - dbt_analytics/models/1_staging/yfinance/_yfinance_staging.yml
  - tests/ingestion/test_market_onboarding.py
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/active_work.md

decisions_reserved:
  - The eleven corrected names below are read directly off yfinance `longName` for each
    ticker, same source and method as the audit that found them. Not re-litigated here.
  - **Whether to also build a name-vs-`info_long_name` audit guard is NOT decided here.** That
    would have caught all eleven on its own; the two existing CI guards only caught two of them.
    It is a second, separable mechanism (a check, not a correction), left for its own task so
    this one stays reviewable. Flagged, not built.
  - **The raw seed CSVs are NOT edited.** The owner's instruction was "corrected in a dbt
    model, not by hand." `storage/seeds/jp_nikkei225/constituents.csv` keeps its wrong names
    at the source; the correction lives entirely in the dbt layer. Consequence: the existing
    `KNOWN_DUPLICATE_SEED_NAMES` allowlist in `tests/ingestion/test_market_onboarding.py`
    (the `mitsuiosklines` / `asahigroupholdings` entries) is UNCHANGED by this task and stays
    accurate: it describes the raw seed, which this task does not touch. An earlier filed-task
    draft said those entries should be removed once the duplicates are "gone"; that was written
    against a hand-edit design the owner has since ruled out, and is superseded by this.

done_when:
  - `company_name_overrides.csv` has eleven rows, `(market_code, ticker)` -> corrected
    `company_name`, for 3407, 6908, 6976, 8005, 8804, 8830, 9005, 9008, 9009, 9101, 9412 in
    `jp_nikkei225`.
  - A new staging model exposes the seed as a 1:1 source mapping (`docs/layering.md`'s staging
    rule), grain-tested (`unique_combination_of_columns` on market_code+ticker, `not_null` on
    all four columns).
  - `base_yf__constituents` left-joins the override onto the deduped constituent relation and
    coalesces `override.company_name` ahead of the seed's own `company_name`, so the corrected
    name is what reaches `dim_stock`'s existing `coalesce(c.company_name, f.info_long_name)`
    unchanged. `dim_stock.sql` itself is NOT edited: the fix lands upstream of it by
    construction, which was one of the two open questions from the prior contract and is
    resolved by this design rather than by editing core.
  - `_yfinance_staging.yml`'s `company_name` column description ("may be overridden in core")
    is corrected: the override happens in `2_base`, not `3_core`.
  - **Split the way `tests/README.md` requires**, not the way the original filed-task draft
    assumed: "the transformation layer is tested in dbt, not Python." So the SQL mechanism
    (join + coalesce actually replacing the name) is a dbt `unit_tests:` pair in
    `_yfinance_base_unit_tests.yml` against `base_yf__constituents`, mutation-proven (reverting
    the coalesce to the seed's own name fails the override-wins test). The seed DATA's
    consistency with the raw constituent file is a plain-file check in `tests/ingestion/`
    instead of a dbt test, because CI's `dbt build` runs against a synthetic fixture database
    that gives every market the same made-up tickers, so a dbt-side relationships test would
    report all eleven real overrides as "dead" and fail in CI regardless of correctness. Three
    tests, all mutation-proven: no duplicate `(market_code, ticker)`; every override ticker
    exists in `storage/seeds/jp_nikkei225/constituents.csv`; the file covers exactly the eleven
    audited tickers.
  - `dbt build --project-dir dbt_analytics --profiles-dir . --full-refresh` green (against the
    CI fixture DB; the eleven real-ticker rows are inert there and that is expected, see above).
  - `pytest` green, no other test touched or weakened.
  - `check_layer_contract.py`, `check_dbt_tests.py`, `check_dbt_documentation.py`,
    `check_dbt_sql_structure.py`, `check_registry_var_sync.py` all green.
  - No em dash or en dash on any added line.

impact_map:
  - `base_yf__constituents` gains a left join and a coalesce; its grain (`market_code, ticker`)
    is unchanged, row count is unchanged (the join is on the override's own unique key, so it
    can only replace a value, never fan out a row).
  - `dim_stock` is unaffected in code; its output changes for exactly eleven `jp_nikkei225`
    rows once real data flows through (not observable against CI fixtures).
  - Ran `dbt ls --select base_yf__constituents+ --resource-type model` before implementing:
    `dim_stock`, then `int_stock__card_metrics`, `int_stock__sector_benchmarks`,
    `mart_stock_cards`, `mart_stock_eligibility_gaps`. `dim_stock` is the only direct consumer
    of `company_name`; the rest read sector/currency/metrics from `dim_stock`'s output and
    never touch the name itself, so no other model's logic is affected.
  - Card headlines for 3407, 6908, 6976, 8005, 8804, 8830, 9005, 9008, 9009, 9101, 9412 change
    on the next production run that rebuilds `dim_stock`. No already-shipped number (verdict,
    metric, benchmark) changes: this touches only a display string.

amendments:
  - 2026-08-28: superseded the "remove the allowlist entries" instruction in the originally
    filed task (task_86486bc2), which assumed a hand-edited raw seed. The owner's actual
    decision (dbt-model correction, not by hand) makes that instruction wrong; corrected here
    under decisions_reserved.
