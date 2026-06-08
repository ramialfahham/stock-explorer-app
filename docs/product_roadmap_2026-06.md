# Product roadmap — post-premortem (2026-06)

Derived from premortem analysis and [`north_star.md`](north_star.md). **Product before platform expansion.**

## Success criteria (6 months)

| # | Criterion | Status (2026-06) |
|---|-----------|------------------|
| 1 | First-time user saves one company on first visit and finds it after hard refresh | **Shipped** — localStorage Save/Not now, landing page |
| 2 | Weekly pipeline green; UI shows data freshness date | **Partial** — `snapshot_date` on card + browse rows; run export after merge for production data |
| 3 | Discover feels intentional — scoped explore, not opaque global queue | **Shipped (v2.3)** — S&P 500 default, filters, browse + walk, menu pool stats |
| 4 | Less than one day per month on infra firefighting | **Ongoing** — monitor CI + Supabase migrate |

---

## Shipped (2026-06)

### UX foundation (#34–#40, UI v2)

- Streamlit theme + dark editorial card layout
- First-run landing (**Stock Explorer** branding)
- Card layout (`card_ui.py`), metric education panel
- Navigation, `snapshot_date` freshness, eligibility monitoring baseline

### Card enrichment (UI v2.2)

| Deliverable | Notes |
|-------------|--------|
| Sector glossary + headline | Plain-English sector context on every card |
| Visible metric gloss | One line under each metric value |
| Median primer + benchmark dedupe | No color coding; compare panel in expand |
| Company business summary | Pipeline → mart → card blurb (`business_summary`) |
| On-demand live quote | yfinance tap on footer; not in mart |
| localStorage mount fix | Single `local_storage_manager` mount per run (#56) |
| Hero market (S&P 500) | US-first walk when “Surprise me worldwide” is off |

### Explore + learn (UI v2.3)

| Deliverable | Notes |
|-------------|--------|
| Compressed Discover header | `{n} to explore · {saved} saved`; pool breakdown in ⋯ menu |
| Progressive disclosure | Median/benchmarks in “How we compare”; hidden when peers &lt; 8 |
| Hero metric spacing | Mobile stack + padding |
| Landing revisit | **How Stock Explorer works** in menu (does not clear Save) |
| Market + sector filters | Default S&P 500; client-side on mart export |
| Browse + scoped walk | List in expand; scope-aware position copy; **Not now** label |
| north_star v1.2 | Explore model, Saved habit, Saved-only news deferral |

---

## Sequencing — next

```mermaid
flowchart LR
  Ops1[Pipeline + export health]
  Phase2[Saved-tab news spike]
  Ops1 --> Phase2
```

| Priority | Work | Scope |
|----------|------|--------|
| P0 | **Ops** | Weekly pipeline green; migration 004 applied; re-export for `business_summary`; refresh eligibility baseline after healthy run |
| P1 | **Phase 2 spike** | News on **Saved tab only** — after v2.3 feels good in manual smoke |

---

## Explicitly out of scope (until success criteria met)

- New market activation beyond registry
- Auth / cross-device sync
- News on Discover cards
- Frontend migration off Streamlit
- Color-coded benchmark badges (north_star v1)
- dbt-side market/sector filters (~800 rows — client filter sufficient)

---

## Premortem guardrails

- **Do not** add markets + auth + news + full redesign in parallel.
- **Do not** ship metrics without plain-language + Learn copy.
- **Do not** show global queue totals that confuse beginners.
- **Exit trigger for Streamlit:** if next major feature needs >2 weeks of Streamlit hacks, spike a real frontend.

---

## Verification checklist (each release)

- Manual smoke on Streamlit Cloud after merge
- Save / not now / hard refresh still works (localStorage)
- Mobile-width scan: company + 3 hero metric values visible without scroll
- Discover loads without `StreamlitDuplicateElementKey`
- Small-sector cards show no orphan benchmark line on card face
- Menu **How Stock Explorer works** reopens landing without clearing Save

---

## Ops commands (reference)

```bash
# After healthy pipeline run — refresh eligibility baseline
python scripts/check_eligibility_baseline.py --duckdb-path storage/stock_data.db --write-baseline

# Re-export mart to Supabase (after dbt build)
python scripts/export_to_supabase.py
```
