# Review

diff_sha256: 5fdcfe571c62a61b659960e2d11cb387e3b6e422e80c561034412523e22aea9b

## scope-auditor

VERDICT: PASS
risks_checked:
- Per-metric count logic correctly applies the same filter as the aggregates (e.g.,
  positive-equity check for debt_to_equity/statement_roe_pct), ensuring the count
  accurately represents coverage and prevents rendering on insufficient real values.
- All 10 metrics gate on their own dedicated n_<metric> count in the combined CTE, not a
  shared sector_peer_count, preventing cross-metric gate contamination.

## analytics-engineer-reviewer

Note, not a blocker: `_intermediate.yml`/`_marts.yml`'s ~50 `sector_median/min/max/q1/q3_*`
column docs still say "Null when sector_peer_count < 8," now stale against the corrected
gate. Contract records this as an explicit owner decision (2026-09-23) to land the SQL fix
first and re-scope issue #23's doc fix against the corrected behavior afterward -- not a
silent gap.

VERDICT: PASS
risks_checked:
- Same-window integrity for the two negative-equity-filtered metrics: confirmed
  n_debt_to_equity/n_statement_roe_pct use the byte-identical filtered CASE expression as
  their median/min/max/quantile_cont siblings -- the per-metric count measures exactly the
  population feeding those stats, no numerator/denominator mismatch.
- Complete migration off the blanket gate: confirmed all 48 case blocks in `combined` gate
  on m.n_<metric> >= peer_threshold, none still reference c.sector_peer_count.
  sector_counts' count(*) is untouched and still exposed as-is.
- Unit-test math verification: hand-recomputed DuckDB's linear-interpolation quantile
  formula for all new/changed fixtures -- all match. Confirmed the four untouched
  pre-existing tests have full per-metric coverage (n_metric == sector_peer_count), so none
  regress under the new gate.
- Downstream reach: mart_stock_cards.sql only passes through the existing sector_*
  columns and sector_peer_count unchanged; does not expose any new n_<metric> column.
  Layer placement holds per docs/layering.md.
