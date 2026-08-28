# Review

diff_sha256: 5db6d20b9e54fbd07d9936c53cabdb4790bf2caca96de465f365205df1f4242c

Three review rounds. Required reviewers per routing (`.claude/review_routing.json`):
scope-auditor (always), analytics-engineer-reviewer (`*.sql`, `*.csv`, `*dbt_project.yml`,
`dbt_analytics/*.yml`), cto-reviewer (`tests/*`). data-engineer-reviewer and
equity-analyst-reviewer are not routed to this diff's file set.

**Reviewer dispatch:** the plugin's reviewer agent types are not registered as dispatchable in
this session, so each ran as a general-purpose agent instructed to read its own role file
verbatim first. Cold, blinded, read-only input; the staged index was frozen to a patch file and
sha256 before every dispatch and never moved while reviewers were running.

**Final verdicts (round 3, the commit gate):** scope-auditor PASS, analytics-engineer-reviewer
PASS, cto-reviewer PASS.

## What this is

Fixes eleven wrong company names on live `jp_nikkei225` cards by building the seed-to-staging-
to-base name-override mechanism the owner decided on 2026-08-28 (seed files are used for this
kind of correction elsewhere in the org; the mapping becomes a staging model, the actual
correction happens in base). New seed `dbt_analytics/seeds/company_name_overrides.csv` (11
rows), new staging model `stg_manual__company_name_overrides` (1:1 pass-through), and a
left-join + coalesce added to `base_yf__constituents.sql` in 2_base. Two dbt `unit_tests:` cover
the join/coalesce mechanism; three Python tests in `tests/ingestion/test_market_onboarding.py`
cover the seed data's consistency with the raw constituent file (kept out of dbt because CI's
synthetic fixture data would make a dbt-side relationships test permanently red regardless of
correctness). The raw seed CSV is deliberately untouched; the correction lives entirely in the
dbt layer.

## Round-by-round findings and fixes

**Round 1**: scope-auditor and analytics-engineer-reviewer both independently found two em
dashes on added lines in `.claude/task/contract.md`, plus a one-day date typo in its
`amendments:` section (2026-08-29 instead of 2026-08-28). cto-reviewer's first attempt was
killed mid-review and redispatched fresh; the redispatch found the same em-dash/date issue plus
three more, all in its own lens: an import-CTE grouped after a transform CTE in
`base_yf__constituents.sql` (violates `docs/engineering_standards.md` §1.1), a docstring in
`test_market_onboarding.py` that misdescribed the join mechanism (claimed `qualify row_number()`
would dedupe a duplicate override key; it's actually a plain left join that would fan out the
row), and a unit-test fixture pair that could not distinguish a correct compound-key
(market_code, ticker) join from a regression that dropped market_code and matched on ticker
alone: a real risk given Nikkei's bare-numeric tickers. All five fixed: dashes to colons, date
corrected, CTE reordered, docstring corrected, and a same-ticker/different-market decoy row
added to the "no override" unit test. The market_code fix was mutation-tested live (dropping the
predicate made the strengthened test fail as expected, confirmed by two independent reviewer
instances plus my own run) before being confirmed as the fix.

**Round 2**: scope-auditor and analytics-engineer-reviewer both passed clean. cto-reviewer
independently re-verified all five round-1 fixes were genuine (not just present in the diff but
functionally correct, including a live re-run of the market_code mutation test) and found two
new documentation-accuracy defects on a fresh pass: the contract's done_when bullet claimed
`not_null` on "all three columns" of the new staging model when the seed actually has four
columns (market_code, ticker, company_name, reason), and `_yfinance_base.yml`'s column-level
description for `company_name` on `base_yf__constituents` was stale: it didn't mention the
override join even though the model-level description three lines above it did, and the sibling
description in `_yfinance_staging.yml` had already been corrected. Both fixed: "three columns" →
"four columns"; the base-layer column description now states the override mechanism.

**Round 3**: all three required reviewers passed clean on a fresh, cold, independent pass, with
explicit re-verification (not trust) of every prior-round fix plus new hunting for anything
missed. No further findings.

## scope-auditor
VERDICT: PASS
risks_checked:
- Every changed file falls inside `scope_paths`; the raw seed CSV and `dim_stock.sql` are
  untouched as the contract requires.
- `KNOWN_DUPLICATE_SEED_NAMES` allowlist is untouched (diff to the test file is pure append).
- `done_when` bullets match the diff exactly, including the corrected four-column count.
- No em/en dash on any added line (byte-scanned every `+` line in the frozen patch).
- All eleven override rows target real, currently-wrong rows in the raw seed on disk.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- Join cardinality/fan-out: the override side is uniqueness-tested at both seed and staging
  layers, so the left join in `base_yf__constituents` can only replace a value, never fan out a
  row; confirmed via `dbt build --full-refresh` (122/122 green including both unit tests).
- Both unit tests are genuinely mutation-proof, not vacuous: the override-wins test fails if the
  coalesce order or join type changes; the no-override test fails if the join predicate drops
  market_code (a real risk given Nikkei's bare-numeric tickers), confirmed live.
- `docs/engineering_standards.md` §1.1 CTE-ordering compliance in `base_yf__constituents.sql`;
  `sqlfluff lint` clean.
- Layering compliance (`docs/layering.md`): staging model is a pure 1:1 pass-through; the
  correction is entity resolution, which belongs in 2_base.
- Documentation (`_yfinance_base.yml`, `_manual_staging.yml`, `_seeds.yml`,
  `_yfinance_staging.yml`) complete, accurate, and internally consistent.

## cto-reviewer
VERDICT: PASS
risks_checked:
- Re-run/interruption safety: seed load is idempotent under `--full-refresh`; staging/base are
  deterministic views; the join is on the override's own unique key.
- New-mechanism justification: this reuses the repo's existing seed convention
  (`metric_catalogue` already follows the same shape), not a novel mechanism, and is an
  owner-authorized pattern per the contract's `decisions_reserved`.
- Test-taxonomy placement (`tests/README.md`): SQL mechanism logic in dbt `unit_tests:`, seed-
  data consistency in Python: correctly split, and the CI-fixture-collision justification for
  keeping the data check out of dbt was verified against `scripts/seed_ci_raw_fixtures.py`
  directly, not just asserted.
- Full gate suite green: `pytest` (394 passed), all five `check_*.py` scripts, `dbt build
  --full-refresh` (122/122), `dbt docs generate` + `check_dbt_documentation.py`.
- No new dependency, no CI/hook/plugin config touched, no secrets, no cost or cadence change.
