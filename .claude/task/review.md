# Review

> DISPOSABLE. **Owns:** THIS task's reviewer verdicts and the staged-diff hash they were
> given against.
> **Never:** a rule. Overwritten by the next task.

diff_sha256: de406d0e1032c1563a1fe45ca1aebdb73108d5419edd608c770a6a9a12fe5e09

Two reviewers, by routing: scope-auditor (`always`), equity-analyst-reviewer
(`docs/data_contract.md`). One round.

## What shipped

`docs/data_contract.md`'s "Supabase export" heading now reads "## Supabase export --
`mart_stock_cards` table", and the Grain line explicitly distinguishes the Postgres table's
three-column grain from the dbt model's own narrower grain -- a finding three reviewers had
already flagged in an earlier MR, never fixed until now.

## Round 1

scope-auditor: PASS. equity-analyst-reviewer: PASS -- cross-checked the new wording verbatim
against `dbt_analytics/models/5_marts/_marts.yml`'s own model description, confirmed the
paraphrase is exact with no invented detail, and swept the rest of `docs/data_contract.md`
for other grain mentions that might now contradict it (none do).

## scope-auditor

VERDICT: PASS

## equity-analyst-reviewer

VERDICT: PASS

## Owner decisions

Fix per the exact wording already agreed when this was first flagged (add "table" to the
heading) -- no new decision needed.
