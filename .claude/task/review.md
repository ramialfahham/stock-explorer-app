# Review

diff_sha256: 9a1e73d2e24483ddf79ec8219680467a74d6079b6016750cb086656a5c50470a

Four reviewers, required by routing: scope-auditor (`always`), analytics-engineer-reviewer
(`*.sql`, `dbt_analytics/*.yml`), cto-reviewer (`scripts/*`, `tests/*`), equity-analyst-reviewer
(`docs/data_contract.md`). Many rounds; each section summarises rather than enumerating, and
only the final verdict is a bare line.

Three reviewers were deliberately re-run at the end against this exact hash, because their
standing verdicts were given on earlier artifacts. cto-reviewer had passed a design that was
subsequently replaced; equity-analyst-reviewer and analytics-engineer-reviewer had passed
versions of files that changed afterwards. Recording those older verdicts against this hash
would have been the same class of unverified claim the cycle spent most of its rounds catching.

## What shipped

`dbt_analytics/tests/assert_percent_scale_passthroughs.sql`: for each of `dividend_yield_pct`,
`revenue_growth_yoy_pct` and `roe_pct`, per market, on `int_stock__card_metrics`, assert the
median ABSOLUTE value falls inside a two-sided band (0.5-50, 1.0-100, 1.0-200), with a sample
floor of `populated_count >= 5`.

Mutation-verified, and re-run independently by analytics-engineer-reviewer rather than taken
from the author: baseline 0 rows; all 6 cases (three metrics x two directions, one market each)
caught, each returning exactly one row naming the offending market and metric.

`dbt build` 127/127, `pytest tests/ -q` 604 passed, `sqlfluff lint` clean,
`check_dbt_sql_structure.py`, `check_dbt_tests.py` and `check_eligibility_baseline.py` all
green.

## The design error that mattered

Round 1 shipped a single-metric, pooled, signed median over the mart with a LOWER bound. Every
part of that was wrong, and the bound was the serious one. `dividendYield` arrives from Yahoo as
a percent (a units flip makes values 100x SMALLER), but `revenueGrowth` and `returnOnEquity`
arrive as fractions and the model multiplies by 100 (a flip makes them 100x LARGER, moving the
median AWAY from a floor). analytics-engineer-reviewer mutation-proved the guard was blind on
two of three metrics, including the only user-visible one. The author's own mutation test had
divided by 100 for all three, validating a direction that cannot occur for two of them.

## The pattern worth recording

The SQL was settled and independently verified early. Almost every subsequent round found a
FALSE CLAIM in the prose describing it, and several were introduced by the previous round's
fix. Three of those were reviewer observations adopted verbatim without being traced to source:
that pre-revenue rows are excluded from the mart (they are not; `mart_stock_cards.sql:99` is a
join condition, not a row filter), that `stmt_total_revenue <= 0` nulls the growth metric (it
sets the `company_type` label only), and that removing two fixtures would leave CI green (it
trips the 15% total eligible floor). A reviewer's finding is a lead, not evidence.

## scope-auditor

Found, across rounds: a comment block violating §1.2 three separate times (5 lines, then 3,
then 4 in a different file) while the contract claimed compliance; a date stamp inside SQL; an
ambiguous path reference; the handover left unmodified so the follow-up work would not have
survived the session; margin evidence measured on the wrong population; a broken markdown table
in the section the SQL comment cites; the binding market quoted as the loose extreme rather than
the binding one for dividends, which is an arithmetic error not a wording one; a population-skew
claim false in three ways; and a contamination direction stated backward for the margins
actually quoted. All fixed and re-verified.

VERDICT: PASS
risks_checked:
- Every edited path inside `scope_paths`, with three additions recorded as amendments
  (`frontend/overflow_menu.py` equivalent for this task: `docs/data_contract.md`,
  `docs/metric_audit.md`, `tests/tooling/test_audit_mart_vs_yfinance.py`), each justified as
  fallout rather than widening.
- No em/en/figure dash on any added line, scanned from a file with explicit UTF-8 rather than
  through Python stdin. Two `docs/data_contract.md` lines and one `_intermediate.yml`
  description that previously CONTAINED em dashes were rewritten to the repo's `--` convention,
  since editing them makes them added lines.
- `.claude/active_work.md` under its 32,000-byte injection cap throughout, with merged history
  collapsed three times to make room.
- No §6 decision taken unilaterally: the audit script was NOT made to run live in CI, no
  coverage/fill-rate assertion was smuggled in, and no metric definition, label, format or
  shipped number moves.

## analytics-engineer-reviewer

Found the decisive design error (one-sided bound blind on two of three metrics), a sample-floor
predicate that was a provable no-op AND failed on correct data, a pooled median that could not
see a single-market flip, a signed median that understates scale for signed metrics, and a
false "a flip divides each median by 100" claim in the docs.

VERDICT: PASS
risks_checked:
- Guard behaviour re-derived independently at the final hash, not accepted: baseline 0 rows, all
  6 mutation cases caught with the correct market and metric named.
- Layer placement confirmed correct on `4_intermediate`, which `docs/layering.md` assigns
  "expected ranges", and which is the only place `roe_pct` exists.
- Every claim in the rewritten `_intermediate.yml` description traced to source: exported
  (`mart_stock_cards.sql:33`, `export_to_supabase.py:52`), stored
  (`008_financial_card_metrics.sql:9`), absent from all eligibility branches, absent from
  `metric_catalogue.csv` and `frontend/metrics.json`.

## cto-reviewer

Established by git archaeology that the `0.02 -> 2.0` fixture change was a genuine correction
rather than a fixture bent to make a test pass: the two fixtures were written either side of the
percent discovery and had contradicted each other for two months. Found that the recorded
silent-skip reproduction was false and supplied the correct one.

VERDICT: PASS
risks_checked:
- Fail direction is fail-closed: a failing singular test aborts `dbt build` before
  `export_to_supabase.py`, so flipped data cannot reach Supabase.
- The sample floor has a REACHABLE silent-skip path with one fixture row of margin, recorded
  with a reproduction that was executed rather than reasoned about.
- `--fail-on-drift` gains a false-positive source (a 25% relative threshold on a 2dp-quantised
  sub-0.05 value, on a pilot ticker), unreachable in CI because CI passes `--offline`. Recorded.
- Mutation residue from the reproduction run confirmed cleanly restored: working tree equals
  index, one expected hunk.

## equity-analyst-reviewer

Confirmed the per-market distributions are financially plausible and that their cross-market
ordering is itself evidence the metrics are correctly scaled today (Australia highest on yield
via franking credits, US lowest via buybacks). Found that `docs/data_contract.md` stated the
Yahoo percent convention as unqualified fact in the very file recording that it is not
universal, and that the band margins were measured on a population known to be contaminated.

VERDICT: PASS
risks_checked:
- Upper bounds safe against real market conditions for the nine registered developed markets;
  the 100 ceiling on revenue growth is inflation-naive and would fire on correct data in a
  hyperinflationary index, which is a market-onboarding trap rather than a current defect.
- Floors safe against a dividend-suspension wave: the non-zero filter removes suspenders from
  the population rather than depressing the median, and a crash raises survivors' yields.
- `statement_roe_pct` accepted as a band-setting proxy for the unexported `roe_pct`, with the
  proxy status stated rather than presented as a measurement.
- Direction-of-bias arithmetic recomputed for both quantities: contamination inflates the quoted
  flip margin (14.2x observed against 13.9x clean) and understates current headroom. Both ~2%.

## Standing observations, recorded not fixed

- The unqualified "dividendYield is already in percent" claim survives in five dbt YAML
  descriptions outside `scope_paths`, plus one standing-decision line in
  `.claude/active_work.md`. Locations are recorded on issue #10; a partial sweep inside this
  branch would have been cosmetic.
- `docs/metric_audit.md`'s new row says the audit set "matches what the scale guard covers",
  which is not literally true in either direction. The same sentence names the dbt test as the
  real guard, so nothing depends on the imprecision.
- Production holds `dividendYield` in mixed units today (issue #10). A per-market median guard
  structurally cannot see per-row mixed units; the limitation is documented rather than implied.
