# Task contract
> DISPOSABLE. **Owns:** THIS task's objective, `scope_paths`, reserved decisions and
> `done_when`.
> **Never:** anything that outlives the task. Overwritten by the next task.

objective: Evict stale cards from the deck. A company whose newest snapshot is 28 or more days
  behind its market's newest snapshot (two missed scheduled runs) leaves the Discover deck
  instead of showing old numbers as current. Resolves the eviction half of active_work.md open
  item 1; the revenue-growth fallback half is declined for the MVP.

scope_paths:
  - supabase/migrations/020_current_cards_view.sql
  - frontend/supabase_cards.py
  - tests/frontend/test_supabase_cards.py
  - tests/tooling/test_current_cards_view_guard.py
  - docs/data_contract.md
  - docs/supabase_setup.md
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/active_work.md

decisions_reserved: settled by the owner in-thread before implementation -- evict by age (yes),
  cutoff two missed runs, about 4 weeks (28 days), mechanism a Postgres view rather than a
  frontend filter, a stale saved company is simply hidden from Saved (no new copy), no
  revenue-growth fallback.

done_when:
  - Migration 020 creates `public.current_cards` (security_invoker, one row per company, 28-day
    rule relative to the company's own market) and grants select to the roles 011 grants on the
    table.
  - `fetch_deck_rows` reads the view; `fetch_card_detail` and the business_summary probe keep
    reading the table (the detail backfill needs every snapshot).
  - A tooling test fails when a later migration alters `mart_stock_cards` without recreating
    the view, proven by a synthetic violating migration.
  - The view's SELECT, run read-only against production, keeps 1047 of 1050 companies and
    drops exactly BXB/RMS/SPK; the migration applied and rolled back in one transaction runs
    clean.
  - `pytest tests/`, em-dash and narrative-date checks pass; review cycle run; MR opened. Not
    merged.
