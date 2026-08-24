# Product roadmap — post-premortem (2026-06)

Derived from premortem analysis and [`north_star.md`](north_star.md). **Product before platform expansion.**

**Last refreshed:** 2026-06-09 (through PR #125).

## Success criteria (6 months)

| # | Criterion | Status (2026-06-09) |
|---|-----------|---------------------|
| 1 | First-time user saves one company on first visit and finds it after hard refresh | **Shipped** — localStorage Save/Not now, landing page |
| 2 | Weekly pipeline green; UI shows data freshness date | **Shipped** — `snapshot_date` on card footer + export health gate (#116); monitor weekly CI |
| 3 | Discover feels intentional — scoped explore, not opaque global queue | **Shipped (v2.3+)** — filters + walk + Search; pool stats in ⋯ menu |
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
| Yahoo Finance footer link | `st.link_button` opens quote page in new tab |
| localStorage mount fix | Single `local_storage_manager` mount per run (#56) |
| Hero market (S&P 500) | US-first in round-robin when all markets in scope |

### Explore + learn (UI v2.3)

| Deliverable | Notes |
|-------------|--------|
| Compressed Discover header | Stats line + pool breakdown in ⋯ menu |
| Progressive disclosure | Median/benchmarks in “How we compare”; hidden when peers &lt; 8 |
| Hero metric spacing | Mobile stack + padding |
| Landing revisit | **How Stock Explorer works** in menu (does not clear Save) |
| Market + sector filters | Default **All markets · All sectors**; client-side on mart export |
| Scoped walk | **Next company** within filters; scope-aware position copy; **Not now** label |
| north_star v2.3 | Explore model, Saved habit |

### UX polish sprint (June 2026, #116–#125)

| Deliverable | Notes |
|-------------|--------|
| Export health gate | Pre-export `business_summary` fill check (#116) |
| Saved headlines | Auto-load up to 3 on focus; disclosure for long titles (#119–#120) |
| Discover card trim | Removed Quick check, live-quote UI, browse expander (#121) |
| Saved clickable rows | Full-row tap; no separate Open button (#122) |
| Nav row menu | ⋯ inline with tabs on mobile — horizontal flex, not `st.columns` (#124) |
| Saved list typography | Left-aligned HTML rows + invisible tap layer (#125) |
| Metric filters attempt | Shipped #117, reverted #118 — backlog #109 |

---

## Sequencing — next

```mermaid
flowchart LR
  Ops[Weekly pipeline green]
  P2[Phase 2 backlog]
  Ops --> P2
```

| Priority | Work | Scope |
|----------|------|--------|
| P0 | **Ops** | Weekly pipeline green; migrations applied; post-merge export + eligibility baseline |
| P1 | **Discover metric filters** | Mobile-friendly design before re-shipping (#109) |
| P2 | **Stickiness** | Filter persistence, Not now review list, two-company saved compare |
| P3 | **Depth** | Reuse disclosure pattern in Learn panel (#112) |

---

## Explicitly out of scope (until success criteria met)

- New market activation beyond registry
- Auth / cross-device sync
- News on Discover cards
- Discover browse list (removed)
- On-card live quote (removed)
- Frontend migration off Streamlit
- Color-coded benchmark badges (north_star v1)
- dbt-side market/sector filters (~800 rows — client filter sufficient)

---

## Premortem guardrails

- **Do not** add markets + auth + news + full redesign in parallel.
- **Do not** ship metrics without plain-language + Learn copy.
- **Do not** show global queue totals that confuse beginners.
- **Do not** put list row copy in visible `st.button` labels (Streamlit centers text).
- **Exit trigger for Streamlit:** if next major feature needs >2 weeks of Streamlit hacks, spike a real frontend.

---

## Verification checklist (each release)

- Manual smoke on Streamlit Cloud after merge
- **Mobile header (~480px):** brand + tagline; **⋯ inline with Discover / Saved / Search** (not on its own row); overflow menu on all tabs
- Save / not now / hard refresh still works (localStorage)
- Mobile-width scan: company + sector + health verdict visible without scroll, at least the first metric value above the fold (no hero/tier split); **Save reachable** on Discover
- Card scannable in ~30 seconds with learn panel closed
- Discover loads without `StreamlitDuplicateElementKey`
- Small-sector cards show no orphan benchmark line on card face
- Menu **How Stock Explorer works** reopens landing without clearing Save
- **Saved tab:** left-aligned bordered rows → tap opens focus; headlines load; **← Back to list** works; no horizontal scroll
- Search tab: ticker lookup still renders eligible snapshot
- Card footer: freshness date + **Yahoo Finance** link opens correct quote page in new tab
- Company description: preview static; **Read full description** toggles expand only

---

## Ops commands (reference)

```bash
# After healthy pipeline run — refresh eligibility baseline
python scripts/check_eligibility_baseline.py --duckdb-path storage/stock_data.db --write-baseline

# Re-export mart to Supabase (after dbt build)
python scripts/export_to_supabase.py

# Pre-export health (business_summary fill)
python scripts/check_export_health.py

# Spot-check business_summary on latest snapshot (service role / SQL)
# e.g. ABNB should have non-empty business_summary on max(snapshot_date)
```
