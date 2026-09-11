# Task contract
> DISPOSABLE. **Owns:** THIS task's objective, `scope_paths`, reserved decisions and
> `done_when`.
> **Never:** anything that outlives the task. Overwritten by the next one.

objective: Fail the build when a catalogued card metric goes mostly null for a market and
  company type. Issue #9, the fill-rate gap, last Tier-1 item.

  A metric feeding eligibility is non-null on every eligible row by construction; the
  displayed-but-not-required metrics can go null wholesale, and every card then shows "n/a"
  with no alarm. The production measurement behind the floor is in the MR description.

scope_paths:
  - dbt_analytics/tests/assert_metric_fill_floor.sql
  - tests/tooling/test_metric_fill_floor.py
  - docs/data_contract.md
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/active_work.md

decisions_reserved:
  - The floor. Owner-set: 50% of eligible cards per `(market_code, company_type, metric)`,
    groups under five rows skipped. A sanity floor between normal gaps (79%) and a dropped
    field (0%), not a metric definition.

done_when:
  - A singular dbt test over `mart_stock_cards` joined to the `metric_catalogue` seed returns
    every `(market_code, company_type, metric_id)` where the metric applies to the type, the
    group has at least five eligible rows, and fewer than half carry a value.
  - A Python test renders the singular test and executes it against an in-memory DuckDB with
    the real catalogue: the metrics it iterates equal the catalogue; five rows at 40% are
    returned, at 60% are not, and exactly half passes; four rows at 0% are skipped; a null
    financial and a null pre-revenue metric are each returned; ineligible rows do not count.
    The types CI fixtures cannot exercise are covered here.
  - Proven on the built tree too: nulling one applicable metric column fails the dbt test.
  - `docs/data_contract.md` states the floor in the percent-scale guard's "What this does NOT
    cover" paragraph, which currently says no fill-rate test exists.

impact_map: A new dbt test node; no model, export or schema change. CI fixtures carry seven
  rows per market, five operating, one financial, one pre-revenue, so in CI only the operating
  groups reach the five-row floor and the six financial and pre-revenue metrics are never
  exercised there; production exercises all three types. Raising the fixture counts would
  widen scope and is the owner's call, to be recorded in the handover commit that follows the
  MR, which also retires the handover's "nothing asserts a fill rate" lines.
