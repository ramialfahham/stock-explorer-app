# Review

diff_sha256: 66715afd882c052f84747b3f69f62ab8b6c935ae9d3497f67b068febb7621a0b
rounds: 1

Works #73 (EXP-1, defect 20; the EXP-2 items 21 and 22 are owner calls, untouched). The column table in
`docs/data_contract.md` gets the two missing rows (`company_founded_year` bigint, `ebit_margin_basis` text; the audit
proposed `integer` for the first, which the dbt contract and migration 006 contradict), and
`tests/tooling/test_schema_copies_agree.py` now compares that table with the migrations. Round 1 (tree 1ee7229):
scope-auditor, platform-reviewer and equity-analyst-reviewer all PASS. Applied after the PASS verdicts: the final newline of the test file (added by the end-of-file hook) and the contract
sentence "no other doc text changes" now names the reworded paragraph. The data contract was 29 bytes under its
context budget, so the paragraph before the table is shortened to fit the two rows; it drops the clause "before
anything downstream ever sees a bad schema".

Coordinator evidence:
- The real document passes the new test; with either new row removed in memory the test reports exactly that column
  ("in the migrations but missing from the data contract table").
- Six mutations of the check, file restored after each, each fails a test: missing row not reported, extra row not
  reported, duplicate not reported, type not compared, section running past the next heading, `id` not excused.
- `pytest tests` 1482 passed, 1 skipped; `check_context_budget.py`, em-dash and narrative-date checks pass.

follow_ups: `supabase/migrations/018_atomic_card_export.sql` lines 68-69 still call the schema a "fourth
hand-maintained copy" of which only the dbt contract is machine-checked (outside scope, a migrations comment: the
owner's call); a test that a changed heading raises; the "except `id`" wording is stricter than the check, which
only excuses `id` when the table omits it.

## scope-auditor

VERDICT: PASS
reviewed_tree: 1ee722930a5429c49bace9257ca1aa8750081e8e
risks_checked:
- The new rows match the dbt contract and migrations 005 and 006, in `EXPORT_COLUMNS` order.
- The shortened paragraph keeps the claim that `dbt build` enforces the contract on every merge request.
wording_fixes: applied.

## platform-reviewer

VERDICT: PASS
reviewed_tree: 1ee722930a5429c49bace9257ca1aa8750081e8e
risks_checked:
- The row pattern matches every row of the real table and none of the header; a changed heading or an emptied table fails loudly.
- The unit tests pin the missing, extra, duplicate and type branches, the section boundaries and the `id` exemption.
wording_fixes: none required.

## equity-analyst-reviewer

VERDICT: PASS
reviewed_tree: 1ee722930a5429c49bace9257ca1aa8750081e8e
risks_checked:
- The two rows and their "nullable" notes are true against `_marts.yml` and the explanation of `ebit_margin_basis`.
- The reworded paragraph still states the contract enforcement truthfully; no metric definition or number changed.
wording_fixes: none required.
