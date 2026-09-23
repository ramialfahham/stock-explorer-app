# Review

diff_sha256: 0ee19ece319623e6a70266233e3a314e4cdb64c1f08807da02d4ca7db3972b5b

## scope-auditor

VERDICT: PASS
risks_checked:
- Per-metric gating logic vs. doc claims: verified `combined` CTE gates each metric on its
  own `n_<metric>` count in the merged SQL; descriptions accurately state "fewer than 8...
  have a non-null <metric>."
- Eligibility gate breakdown and guarantee statements: verified int_stock__card_metrics.sql's
  eligibility CASE confirms which metrics gate which sector types; descriptions correctly
  name the four cases (never-gated, operating-only, financial-only, both + negative-equity
  filter).
- pre_revenue join exclusion claim on mart_stock_cards.sector_peer_count: verified against
  the model SQL's join condition; description correctly names this as the dominant cause.

## analytics-engineer-reviewer

VERDICT: PASS
risks_checked:
- Doc-sync correctness for the per-metric company_type gating claims across all ~50 changed
  columns in both yml files: cross-checked each metric's claimed eligibility category
  against int_stock__card_metrics.sql's eligibility CTE and int_stock__sector_benchmarks.sql's
  n_<metric> counts / per-metric case gate. No inverted condition, no metric assigned to the
  wrong company_type category, no wording drift found in any of the 10 metrics' descriptions
  in either file. The debt_to_equity/statement_roe_pct positive-equity filter is correctly
  described as further reducing their n_<metric> counts below sector_peer_count.
- mart_stock_cards.sector_peer_count's new pre_revenue claim verified against the actual
  (untouched) mart_stock_cards.sql join predicate; confirmed via diff that the
  consumption-layer SQL was not touched, consistent with a docs-only change.
- Doc-checker and parse compatibility: check_null_when_documented's NULL_MENTION_PATTERN
  satisfied by every rewritten description; both yml files parse cleanly; no em/en dash in
  added lines.
