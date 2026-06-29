# Active work — handover

_The next session is handed exactly this file. Keep it current._

## Current task

**Project evaluation → improvement.** The owner is unhappy with the project's state; the lead, concrete
complaint is the **UI: inconsistent design/formatting, cluttered**. We agreed to fix foundations first,
then the UI. In flight: **metric layer Phase 2** — PR #132 (branch `feat/metric-layer-phase2`).

## Status

**Metric layer — Phase 1 MERGED (#131); Phase 2 PR open, awaiting CI + merge:**
https://github.com/ramialfahham/stock-swipe-app/pull/132
- Phase 1 (#131, merged): `metric_catalogue` seed = SSoT → `metrics.json` → `card_copy.py`; card
  byte-identical. The metric layer foundation is in `main`.
- Phase 2 (#132): deletes `scripts/metric_formulas.py` (the Python formula mirror) + the ingestion
  `fundamentals_eligible` counter; reworks `audit_mart_vs_yfinance.py` to validate the mart by
  re-running dbt on fresh raw (no Python formula). Verified locally: 73 pytest, dbt-rerun proven
  end-to-end. No dbt model / mart / Supabase change.

## Next concrete action

Owner reviews + merges #132 (do NOT self-merge). **That completes the metric layer.** Then the main
event — the **UI redesign** (the owner's actual complaint), now sitting on a clean single metric source:
1. Build a redesigned-card MOCK first: one cohesive surface, one disclosure pattern, consistent labels
   incl. the deferred `(TTM)` dynamic-suffix, a real spacing/type scale, words-not-arrows benchmarks.
2. Iterate on the mock, then implement in Streamlit consuming `metrics.json`.
(See the full UI diagnosis below under Context — it's grounded in screenshots of the real card.)

## UI redesign brief (grounded in screenshots of the real card)

The card is what feels "cluttered/inconsistent". Concrete findings:
- **Fragmented into ~5 slabs**, not one card: identity box → an orphaned "‣ Understand these numbers"
  link floating in the gap → metrics box → a bordered "Practice with hypothetical numbers" box → footer.
- **Two disclosure paradigms** on one card: custom HTML `<details>` (gold ▸) vs Streamlit `st.expander`.
- **Basis-leak labels:** "Operating margin (TTM)", "Rev growth YoY (quarter)", "FCF margin (annual)" —
  expose differing time bases on the card face. (The `(TTM)` dynamic-suffix fix was deferred to here.)
- **Tiny ambiguous ↑/↓ benchmark arrows** (direction carries no valence). Replace with words.
- **No spacing scale** (~20 ad-hoc rem values) and **type scale not enforced** (~10 hardcoded sizes) in
  `frontend/styles.py`; plus duplicate/dead CSS (e.g. `.ss-browse-*` from the removed browse list).
Direction: design-system cleanup WITHIN Streamlit first (tokens, one disclosure pattern, one surface,
words-not-arrows, fix the label leak) — not a Streamlit rewrite yet. Mock first, then implement.

## Decisions locked this session

- Metric layer = a dbt-seed `metric_catalogue` (football pattern), built BEFORE the UI mock so the mock
  consumes a single source. See [[no-duplicate-sources]].
- Phase 1 is a ZERO-text-change port; the (TTM) label-leak fix is deferred to the UI work (touches
  metric_school.py — a UX wording change).
- Drift guard is a Python test, not a dbt singular test — repo's §1.1 SQL-structure gate (WITH-first)
  is incompatible with football's jinja introspection style.

## Do NOT

- Do not commit/push to `main`; do not `gh pr merge`. Agent commits need `gitleaks` on PATH (the
  pre-commit hook); export it from the WinGet Packages dir if a commit hook fails to find it.
- Do not reword metric copy (labels/gloss/analogy/learn) — owner content (§6); port verbatim.
- Do not enable ruff-format or broaden the dbt MCP beyond read-only without asking.

## Context / open items

- **Backend fragility (track B):** the deployed app at https://stock-explorer.streamlit.app/ runs on a
  **free-tier Supabase** that pauses after ~7 days idle (DNS drops → the app shows repeated "Could not
  load cards" errors, and renders that error 4× — a real bug: `_ensure_all_cards` is called repeatedly
  per render). It was restored this session (857 eligible cards, healthy coverage). Will recur — decide
  keep-alive vs paid tier vs accept manual restore.
- A separate branch `docs/refresh-june-2026` holds unrelated in-flight docs work (other chat); leave it.
- Throwaway render harness lives in the session scratchpad (`card_preview.py`); not in the repo.
