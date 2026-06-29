# Review

diff_sha256: 6f74ad48f55a7a0b5eede4aed680cd575aa449a97a2729565d6c0dc298599477

## scope-auditor
VERDICT: PASS
risks_checked:
- Every staged path is inside scope_paths (scripts/audit_mart_vs_yfinance.py, scripts/metric_formulas.py [del], ingestion/yfinance/ingest.py, ingestion/main.py, tests/test_audit_mart_vs_yfinance.py, tests/test_metric_formulas.py [del], docs/metric_audit.md, .claude/**). ingestion/main.py was added to scope via amendment (it printed the dropped counter); ci-validate.yml was deliberately NOT changed — the reworked audit keeps the --offline CLI so the existing smoke step still passes.
- impact_map "(none)" holds: no dbt model / seed / mart / Supabase change; the audit and the dropped ingest counter are QA/observability only.
- Raw-only ingestion contract preserved: ingest.py still appends every fetched row; only the in-memory eligibility counter (a dbt-gate mirror) and its helpers were removed — landed parquet is byte-unchanged.
- Verified, not asserted: 73 pytest pass; the shipped dbt-rerun function returns correct metrics; no metric_formulas reference remains in code.

## data-engineer-reviewer
VERDICT: PASS
risks_checked:
- ingest.py no longer computes any metric/eligibility: _effective_net_debt / _has_operating_margin_inputs / _is_card_eligible_raw and the fundamentals_eligible counter are gone; the raw fetch+land path (_fetch_fundamentals_row → rows.append → parquet) is untouched, so ingestion output is identical minus a console stat. main.py print updated to match.
- The audit's temporary raw matches the dbt source schema: yf_fundamentals.parquet is reindexed to FUNDAMENTALS_COLUMNS (the full sources.yml yf_fundamentals column set, missing→null), and yf_constituents.parquet carries the (market_code, ticker, company_name, refreshed_at, source, ingested_at) columns dim_stock needs. active_market_codes is overridden to just the sampled markets so the raw_parquet_union only reads what's present.
- Live fetch reuses the proven ingestion fetch; the dbt rebuild was verified end-to-end (correct forward_pe/ebit/net_debt/fcf for two synthetic tickers). No daily_prices needed (not an ancestor of int_stock__card_metrics).

## cto-reviewer
VERDICT: PASS
risks_checked:
- metric_formulas.py (the Python formula mirror) is deleted with no remaining code references; the dbt model is now the only place metrics are computed.
- The reworked audit invokes dbt via subprocess (shutil.which("dbt"); temp profiles.yml → temp DuckDB; temp raw under TemporaryDirectory, auto-cleaned) and **uses `dbt run` not `dbt build`** to avoid pulling in descendant singular tests (learned during the round-trip proof). It fails OPEN — a failed rebuild prints a warning and yields no drift rows rather than crashing the audit.
- CLI/behaviour preserved: --source/--duckdb-path/--offline/--sample-size/--fail-on-drift unchanged, so the CI offline smoke (`--offline --sample-size 5`) still runs with no fetch/rebuild. pct_drift is a small inlined signed-percent helper (no formula); fail-on-drift and the summary use absolute drift. No secrets; default=str on JSON dump handles dates.
- Verified: offline unit test (mart-side only, no drift columns) + live-path dbt-rerun integration test pass; full suite 73 green. Risk (accepted): live mode needs dbt on PATH — fine for a dev/pipeline QA tool; offline CI never invokes dbt.
