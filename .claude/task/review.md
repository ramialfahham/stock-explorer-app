# Review

> DISPOSABLE. **Owns:** THIS task's reviewer verdicts and the staged-diff hash they were
> given against.
> **Never:** a rule. Overwritten by the next task.

diff_sha256: 6b4b0d5d5196a086a9d7fa817f9684a7c6705d7ba201d9e7531053caf06ec45a

Four reviewers, by routing: scope-auditor (`always`), data-engineer-reviewer (`supabase/*`),
cto-reviewer (`tests/*`), analytics-engineer-reviewer (`*.sql`). Two rounds.

## What shipped

Migration `019` alters every capped `numeric` column on `mart_stock_cards` to plain `numeric`,
finding them in `pg_attribute` and raising if any remain. A test refuses any later migration
that declares `numeric(p,s)`, `decimal(p,s)` or `dec(p,s)`. 650 tests.

## Dev verification, out of band

After `apply_supabase_migrations.py --target dev`, over psycopg2:

```
dev capped: []
prod capped: 10 ['ebit_margin_pct', 'fcf_margin_pct', 'forward_pe', 'net_debt_to_ebitda',
  'revenue_growth_yoy_pct', 'sector_median_ebit_margin_pct', 'sector_median_fcf_margin_pct',
  'sector_median_forward_pe', 'sector_median_net_debt_to_ebitda',
  'sector_median_revenue_growth_yoy_pct']
probe round-trip: 12345678.9
rolled back
```

## Round 1

cto: the guard missed `decimal(p,s)` and `dec(p,s)`, both Postgres aliases that produce the
same capped column; a test asserting substrings of the migration text was theatre. Both taken.
scope-auditor and data-engineer: three sites stated the overflow as a past incident; the repo
records only a risk. Reworded. `supabase_setup.md`'s "complete as of 018" updated.

## scope-auditor

VERDICT: PASS

## data-engineer-reviewer

VERDICT: PASS

## cto-reviewer

VERDICT: PASS

## analytics-engineer-reviewer

Traced the type boundary: DuckDB `double` to Python float to JSON to plain `numeric` is exact
and strictly less lossy than the 4-decimal rounding it replaces; NaN maps to null and every
model division is guarded, so no infinity reaches the payload. `supabase/migrations/` is
outside every sqlfluff path. On `accepted_range`: a definitional bound is the owner's; a wide
sanity guard at `severity: warn` is the engineer's to propose with a measured number.

VERDICT: PASS

## Owner decisions

None taken. Deferred and recorded in the handover: `accepted_range` bounds on the metrics,
which are metric definitions.
