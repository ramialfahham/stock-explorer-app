# Task contract

objective: Fix the SMI legal-name register by adding nineteen `ch_smi` rows to the existing
  `company_name_overrides` seed (built for the Nikkei fix), so `ch_smi` card headlines read as
  trade names like every other market instead of legal-register forms. Owner-approved name list,
  2026-08-28. Does not touch the raw seed CSV, does not touch the Block ticker or any other
  market's names.

scope_paths:
  - dbt_analytics/seeds/company_name_overrides.csv
  - tests/ingestion/test_market_onboarding.py
  - docs/constituent_sources.yml
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/active_work.md

decisions_reserved:
  - The nineteen trade names below were proposed by comparing the current seed against
    yfinance `longName` for each ticker, then presented to the owner as a table and approved
    verbatim ("go ahead with that list"). Not re-litigated here.
  - `KNIN` (Kuehne + Nagel) is deliberately excluded: the seed already carries a trade name,
    yfinance's longName is the more formal one ("Kuehne + Nagel International AG"), so no
    override row is added for it.
  - The raw seed CSV is not edited, same design as the Nikkei fix: `storage/seeds/ch_smi/
    constituents.csv` keeps its legal names at the source; the correction lives entirely in the
    dbt layer via the existing override mechanism.
  - No new mechanism: this reuses `company_name_overrides.csv` / `stg_manual__company_name_
    overrides` / `base_yf__constituents`'s override join exactly as built for the Nikkei fix.
    No schema, model, or test-taxonomy change.

done_when:
  - `company_name_overrides.csv` gains exactly nineteen new `ch_smi` rows: NOVN, ROP, NESN,
    ABBN, UBSG, CFR, ZURN, HOLN, SREN, LONN, SCMN, GIVN, ALC, SIKA, AMRZ, SLHN, GEBN, PGHN, LOGN.
    KNIN is not added. Each row's `company_name` is the owner-approved trade name; each row's
    `reason` states whether the seed's legal name was also factually wrong (NOVN, SREN) or just
    a more formal register of the same issuer (the other seventeen).
  - A new test mirrors `test_company_name_overrides_covers_the_audited_nikkei_defects` for this
    market: pins the exact nineteen `ch_smi` tickers covered, so a future edit can't silently
    drop or add a row without a test noticing.
  - The existing market-agnostic tests (`test_company_name_overrides_target_real_constituents`,
    `test_company_name_overrides_have_no_duplicate_keys`) need no changes; they already loop
    over every market's rows and will cover the new `ch_smi` rows automatically. Confirmed
    they pass with the new rows present, not just assumed.
  - `docs/constituent_sources.yml`'s `ch_smi` note ("the seed name wins over yfinance in
    dim_stock, so SMI card headlines read differently from every other market's. Open, see the
    contract.") is updated to say this is fixed via the override, not left as an open pointer to
    a contract that no longer describes an open problem.
  - No change to `dbt_analytics/seeds/_seeds.yml`, `_manual_staging.yml`, `_yfinance_base.yml`,
    or `base_yf__constituents.sql`: the mechanism already generalizes across markets, so a
    second market's rows need no schema or SQL change. Confirmed by reading each file, not
    assumed from the Nikkei design intent.
  - `dbt build --project-dir dbt_analytics --profiles-dir . --full-refresh` green (against the
    CI fixture DB; the nineteen real-ticker rows are inert there, same limitation as Nikkei).
  - `pytest` green, no other test touched or weakened.
  - `check_layer_contract.py`, `check_dbt_tests.py`, `check_dbt_documentation.py`,
    `check_dbt_sql_structure.py`, `check_registry_var_sync.py` all green.
  - No em dash or en dash on any added line.

impact_map:
  - `base_yf__constituents` gains nineteen more matched override rows on its existing left
    join; no schema, join, or coalesce change. Grain and row count unaffected, same as Nikkei
    (join key is the override's own unique key).
  - Re-ran `dbt ls --select base_yf__constituents+ --resource-type model`: `dim_stock`, then
    `int_stock__card_metrics`, `int_stock__sector_benchmarks`, `mart_stock_cards`,
    `mart_stock_eligibility_gaps`: identical chain to the Nikkei fix, since this is the same
    model gaining more override data, not new logic.
  - Card headlines for the nineteen listed `ch_smi` tickers change on the next production run
    that rebuilds `dim_stock`. No already-shipped number (verdict, metric, benchmark) changes:
    this touches only a display string.

amendments: (none)
