# Review

diff_sha256: 794dcd8362f1381a87251272ee83e42d75081f4c7b7b874b03d3c89d23b0b835

Reviewers dispatched as general-purpose agents reading their own role files (agent types not
registered in this session), cold, read-only, against `.claude/task/review_input.patch`.
Owner decisions taken in-thread before implementation: evict by age; 28 days (two missed
runs); Postgres view over a frontend filter; stale saved companies simply hidden; no
revenue-growth fallback.

Coordinator evidence: the view's SELECT, read-only on production, keeps 1047 of 1050
companies and drops BXB/RMS/SPK (32 days behind). Migration 020 applied and rolled back in one
transaction on Postgres 17.6; as `anon` the view returned 1047 rows, one per company, 79
columns equal to the table's. `pytest tests` 806 passed (excluding
`test_generate_assessments.py`, which cannot import `anthropic` locally on `main` either).

## scope-auditor

Round 1 PASS; round 2 re-run because the guard test changed.

VERDICT: PASS
risks_checked:
- Every staged path in scope_paths; diff matches the owner's decisions, no new copy.
- Guard changes stay within the task.

## data-engineer-reviewer

Round 1 FAIL: the guard missed a drop+create rebuild of the mart (as 002 did) and `alter table
only`. Fixed: comments stripped, `(alter|drop|create) table [if [not] exists] [only]` matched,
synthetic cases added.

VERDICT: PASS
risks_checked:
- DISTINCT ON cannot tie (unique market_code, ticker, snapshot_date); 28-day boundary and
  single-snapshot market correct; security_invoker + grants match 011 and the RLS policy.
- `replace_cards_snapshot()` is DML only, so the dependent view never blocks the export;
  `--target dev` rewrite covers every `public.` in 020.
- Guard: no false positive on 001/002/019; residual (fully interpolated table names in
  dynamic SQL) acceptable for a static check.

## cto-reviewer

Round 1 FAIL: `.claude/active_work.md` item 1 still called eviction undecided; the guard
accepted a commented-out view recreate. Both fixed.

VERDICT: PASS
risks_checked:
- Deck reads the view; detail and the business_summary probe read the table; no UI path
  reaches a stale card's detail; Saved goes through the same deck.
- Mutation check: removing comment stripping fails the new synthetic test.
- Handover item 1 consistent with `docs/data_contract.md`.

## analytics-engineer-reviewer

Routed by `*.sql` (the migration); dispatched after the gate named it.

VERDICT: PASS
risks_checked:
- Layer placement: the rule needs snapshot history, which only Supabase holds (dbt runs on an
  ephemeral DuckDB with the current run only), so the view is the right layer.
- Grain one row per (market_code, ticker); join 1:1 on market_code; `> newest - 28` evicts at
  exactly 28 days; `snapshot_date` is `date`.
- Comments one sentence each, stating why.

## equity-analyst-reviewer

Round 1 only (its file, `docs/data_contract.md`, unchanged since).

VERDICT: PASS
risks_checked:
- 1st/15th arithmetic brute-forced 2000-2100: one missed run 14-17 days, two 28-31, so the
  28-day cutoff separates them exactly.
- Saved and detail paths traced; no remaining "open question" text on eviction.
