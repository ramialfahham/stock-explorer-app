# Task contract
> DISPOSABLE. **Owner:** THIS task's objective, `scope_paths`, reserved decisions and
> `done_when`.
> **Never:** anything that outlives the task. Overwritten by the next task.

objective: Works #73 (EXP-1, defect 20 of the quality-baseline audit re-run; the EXP-2 items 21 and 22 are owner
  calls and stay untouched). The column table in `docs/data_contract.md` section "Supabase export --
  `mart_stock_cards` table" omits `company_founded_year` and `ebit_margin_basis`, which are in the dbt contract,
  `EXPORT_COLUMNS` and the migrations, and the paragraph above it still says those surfaces are hand-maintained
  although `tests/tooling/test_schema_copies_agree.py` now compares three of them. One rule: a documented claim
  that a tool can check is checked, so the doc table joins the schema copies the test compares.

scope_paths:
  - docs/data_contract.md
  - tests/tooling/test_schema_copies_agree.py
  - .claude/active_work.md
  - .claude/task/contract.md
  - .claude/task/review.md

decisions_reserved: Answered by the owner in chat (A): keep the table and extend the test to check it; the table's
  notes stay in the document. No column, type or note of an existing row changes. The paragraph above the table is
  reworded as `changes` lists; no other doc text changes.

changes:
  - `docs/data_contract.md`: two rows added in `EXPORT_COLUMNS` order, `company_founded_year` (bigint, as in the dbt
    contract and migration 006; the audit's proposed `integer` is wrong) after `business_summary`, and
    `ebit_margin_basis` (text) after `ebit_margin_pct`. The paragraph before the table says that
    `tests/tooling/test_schema_copies_agree.py` compares `EXPORT_COLUMNS`, the migrations, the dbt contract and this
    table. The file is 29 bytes under its context budget, so the paragraph's other sentences are shortened to fit
    the two rows and the new sentence; it drops the clause "before anything downstream ever sees a bad schema" and
    keeps the claim that `dbt build` enforces the dbt contract on every merge request.
  - `tests/tooling/test_schema_copies_agree.py`: reads the table under that heading and fails on a column the
    migrations have (except the identity key `id`) that the table lacks, a column the table lists that the
    migrations lack, a column listed twice, and a type that differs from the migrations' type. Tests for each kind
    of disagreement and for the real document.
  - `.claude/active_work.md`: current facts.

done_when:
  - The real document passes the new test, and with `company_founded_year` or `ebit_margin_basis` removed from the
    table in memory it reports exactly that column.
  - Mutation-checked: a missing row, an extra row, a duplicate row and a wrong type each fail a test.
  - `git grep -n "hand-maintained" -- docs` finds nothing that describes the schema copies.
  - `pytest tests -q` passes; `python scripts/check_context_budget.py` passes.

known_limits:
  - The test reads every `| `name` | type |` row between the heading and the next `## ` heading; it compares names and
    Postgres types, not the notes column.
  - It compares the table to the migrations; the migrations are already compared to `EXPORT_COLUMNS` and the dbt
    contract, so all four agree when the test passes.

regression_checklist:
  - The existing three-copy test and its parser behave as before.
  - No row other than the two new ones changes in the table.
