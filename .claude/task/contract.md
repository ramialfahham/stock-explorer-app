# Task contract
> DISPOSABLE. **Owns:** THIS task's objective, `scope_paths`, reserved decisions and
> `done_when`.
> **Never:** anything that outlives the task. Overwritten by the next task.

objective: Real-shaped fixtures (owner request; no issue). CI runs the real ingestion code on
  recorded yfinance and Wikipedia payloads, offline, through dbt to the mart, and compares the
  mart against a committed golden file, so real-data defects fail CI instead of reaching
  production.

scope_paths:
  - scripts/record_ingestion_fixtures.py
  - scripts/replay_ingestion_fixtures.py
  - scripts/check_real_fixture_mart.py
  - tests/fixtures/real/
  - tests/ingestion/test_real_fixtures.py
  - tests/tooling/test_check_real_fixture_mart.py
  - .gitlab-ci.yml
  - docs/operations_guide.md
  - docs/development_workflow.md
  - docs/context_budget.yml
  - .claude/active_work.md
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch

decisions_reserved: settled by the owner in-thread before implementation --
  Go on real-shaped fixtures (a new mechanism: recorder, replay, golden check, CI steps).
  Sample (option A): about 5 real tickers per active market, chosen by type -- ordinary
  companies, a bank or insurer, and known awkward cases:
    us_sp500 AAPL KO JPM BRK.B MRNA | uk_ftse100 SHEL ULVR HSBA BT.A AZN |
    jp_nikkei225 7203 6758 8306 9984 4502 | au_asx200 BHP CSL CBA XYZ FMG |
    de_dax SAP SIE DBK ALV AIR.PA | fr_cac40 MC.PA TTE.PA BNP.PA MT.AS AI.PA |
    nl_aex ASML.AS INGA.AS SHELL.AS PHIA.AS ADYEN.AS | ch_smi NESN NOVN UBSG CFR ZURN |
    es_ibex35 SAN.MC ITX.MC IBE.MC MTS.MC ROVI.MC |
    fi_omxh25 NOKIA.HE NDA-FI.HE KOJAMO.HE KESKOB.HE KALMAR.HE |
    se_omxs30 VOLV-B.ST ERIC-B.ST SEB-A.ST ABB.ST AZN.ST |
    dk_omxc25 NOVO-B MAERSK-A MAERSK-B NDA-DK.CO DANSKE | no_obx EQNR DNB GOGL MOWI TEL |
    ca_tsx60 RY SHOP NA CTC-A.TO ENB | it_ftsemib ENEL.MI ISP.MI RACE.MI STLAM.MI G.MI
  (tickers in the form `load_constituents` returns, i.e. after ticker_overrides).
  Golden file (option A): the replayed mart rows are committed and compared exactly; one
  command regenerates it, so any change to an output number shows in the MR diff.
  Placement (option A): the replay runs inside `validate:full`, no new job.

known_limits:
  - The Wikipedia check asserts the recorded page still parses to (nearly) the committed seed:
    an overlap threshold, not equality, because index membership moves between the seed's
    refresh and the recording.
  - Recordings are frozen; a yfinance shape change after recording is caught only on
    re-record.

regression_checklist:
  - The synthetic CI fixtures and every existing `validate:full` step still run unchanged.
  - Replay needs no network and no credential (it must pass with sockets blocked).
  - No ingestion, dbt or export code changes behaviour; this task only adds a harness.

done_when:
  - `record_ingestion_fixtures.py` records the sample above; files stay under the 500 KB
    pre-commit limit each.
  - `replay_ingestion_fixtures.py` runs the real `ingest_market` on the recordings into a raw
    folder; dbt builds on it; `check_real_fixture_mart.py` matches the golden file; the
    Wikipedia check passes; all offline (tests).
  - `validate:full` runs the replay, the dbt build, the export-health check and the golden
    comparison; the operations guide says how to re-record and regenerate.
  - `pytest tests` passes; review cycle run; MR opened. Not merged.

amendments:
  - Round 1: analytics-engineer and scope-auditor PASS; platform FAIL [broken-guarantee]: no
    test exercised the golden check's mismatch path. Fixed: `test_check_real_fixture_mart.py`
    (changed cell, missing row, extra row, changed columns all return 1 and are listed; cell
    rendering pinned). Also: a weekend `--today` no longer rolls price dates forward (tested),
    `pd.NA` renders empty like NaN (golden regenerated: only `company_founded_year` changed),
    replay docstring and operations-guide wording fixed. Other follow-ups filed.
