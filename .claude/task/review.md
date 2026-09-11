# Review

> DISPOSABLE. **Owns:** THIS task's reviewer verdicts and the staged-diff hash they were
> given against.
> **Never:** a rule. Overwritten by the next task.

diff_sha256: 9b2ff4aa5595875fb08d77c772da891eb1110bb15e53af0049424d0d5127e9dd

Two reviewers, by routing: scope-auditor (`always`), analytics-engineer-reviewer (`*.sql`).
One round.

## What shipped

A macro `raw_parquet_partition` tags each active market's raw file with its folder name beside
the file's own `market_code`; a singular test returns every row where the two differ. The
stored tree passes; `nl_aex`'s constituents file placed under `ch_smi/` fails it. No model
change. `check_layer_contract.py` does not scan `macros/` or `tests/`, so its pass says nothing
about this diff; `sqlfluff` and `check_dbt_sql_structure.py` do cover it and pass.

## scope-auditor

Confirmed the remedy is a test under the existing `dbt build`, not a new mechanism, and that
the override form (folder as authoritative) is correctly reserved. Noted the contract's
"same `market.market_code`" is one step removed for constituents, whose column comes from the
seed CSV; the conclusion holds and the test covers a mis-copied seed too.

VERDICT: PASS

## analytics-engineer-reviewer

Reproduced the mutation independently. Probed that a file missing the column errors rather
than passes, and that a NULL column is reported. Keeps the two macros separate on purpose: the
production union should not carry a test-only branch.

VERDICT: PASS

## Owner decisions

None. Reserved and untouched: making the folder authoritative, which would relabel a
misplaced file's rows instead of failing the build.
