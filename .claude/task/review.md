# Review
> DISPOSABLE. **Owns:** verdicts + diff hash for THIS task's staged change.
> **Never:** narrative of how the round went. Overwritten by the next task.

diff_sha256: 3b177073bf396cd0e524b8ed02755d8773deb665435d688e29c4b319c45bb06d

This task ran four review rounds; only the final passing round is recorded in full below.
Each prior round found a real gap: (1) the new raw-passthrough exemption wasn't documented
in `docs/engineering_standards.md`; (2) 4 of the 32 fixed "Null when" clauses were
factually wrong against the actual SQL (`dim_stock`/`mart_stock_cards`/
`mart_stock_eligibility_gaps` sector/currency); (3) `cash_runway_months`'s pre-existing
description already mentioned "null" but omitted one of three guard conditions; (4)
`ebit_margin_pct`/`ebit_margin_basis` had the same omission, and a much larger family
(~50 `sector_median/min/max/q1/q3_*` columns) shares the same incompleteness -- taken to
the owner directly, deferred as gitlab.com issue #23 rather than fixed here. Full history
in `.claude/task/contract.md`.

## cto-reviewer (final)
VERDICT: PASS
risks_checked:
- `ebit_margin_pct`/`ebit_margin_basis` verified directly against
  `int_stock__card_metrics.sql`'s actual two-branch CASE (9-condition TTM guard,
  3-condition annual guard) -- every condition now named in both files.
- Sector-benchmark family (~50 columns) confirmed genuinely untouched in the diff, not a
  half-fix; GitLab issue #23 exists, is open, and its content matches what the contract
  claims was deferred.
- Fresh sweep of all 34 touched columns for "guard has 3+ conditions, description names a
  subset" -- the pattern that sank two prior rounds -- found no further instances.
- `pytest tests/` (841 passed), `check_no_em_dash.py`, `check_context_budget.py`,
  `dbt parse`, and `check_dbt_documentation.py` all re-run fresh against a manifest newer
  than the staged edits; all pass.
- No new dependency, CI step, or mechanism; `scope_paths`/`decisions_reserved` both
  accurate against the final diff.

## scope-auditor (final)
VERDICT: PASS
risks_checked:
- Sector-benchmark deferral confirmed genuinely whole (zero `sector_median/min/max/q1/q3_*`
  lines touched anywhere in the diff), not partially patched.
- GitLab issue #23 verified to exist and match the contract's description in substance.
- `decisions_reserved` records the defer choice as asked-and-answered, not silently taken.
- `scope_paths` covers exactly the 7 changed files, no stale entries.
- No em-dash/en-dash on any added line; no new dependency/mechanism/cost.

## analytics-engineer-reviewer (final)
VERDICT: PASS
risks_checked:
- `ebit_margin_pct`/`ebit_margin_basis` description verified against the real SQL guards,
  every condition named.
- Full sweep of all 34 touched columns' 3+-condition guards (`price_to_tangible_book`,
  `net_cash_to_ev`, `net_cash_to_market_cap`, `net_debt_to_ebitda`, `fcf_margin_pct`,
  `cash_runway_months`) against their actual SQL -- every guard condition named, no repeat
  of the pattern that failed two prior rounds.
- `check_dbt_documentation.py` re-run against a freshly regenerated manifest, passes clean.
- Flagged one related, out-of-scope finding (`net_margin_pct`/`roa_pct`/
  `statement_roe_pct` have the same incompleteness but never tripped the mechanical check
  since their existing text already contains "null") -- added to issue #23 as a follow-up,
  not fixed in this diff.
