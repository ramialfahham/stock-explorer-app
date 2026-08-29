# North star — Stock Explorer

Product vision and UX principles. When implementation choices conflict, this document wins
for user-facing behavior. Technical contracts live in [`data_contract.md`](data_contract.md).

**Product name:** **Stock Explorer** (in-app and docs). Repo name may remain `stock-swipe-app`.

---

## What we are building

An **explore-and-learn** stock app for **finance-curious beginners** — people with near-zero
prior knowledge who want to **understand companies**, not execute trades.

Each **Company Snapshot** is an analyst-grade overview at low barrier: fundamental metrics for
that company's type, plain language, optional depth. **Discover** is scoped exploration (filter + walk, or **Search** for lookup);
**Saved** is the return habit — your learning list on this device.

**Not investment advice.** Metrics are informational. The app educates; it does not recommend
buys or sells.

**Interaction model:** **Save** and **Not now** (formerly Skip) — not swipe gestures or
dating-app patterns.

---

## Audience and tone

| Dimension | Choice |
|-----------|--------|
| Audience | Beginners — assume no finance vocabulary |
| Motivation | Learn + discover; build a browsing habit via Saved |
| Tone | Fun but serious; education integrated, never gimmicky |
| Builder lens | Dashboard-like reduced overview; v1 optimizes for beginners |

Use **“explore”**, **“save”**, **“not now”**, **“learning list”**. Do not use dating-app
metaphors or opaque queue counters (e.g. global `1/834`) in product copy.

---

## The card: fundamentals by company type

Discovery cards show **fundamentals**, not batch pipeline prices, grouped by analytical lens
(valuation, profitability, growth, solvency, liquidity, cash, returns) so a card reads as one
coherent picture, not a flat list. Which metrics apply, and which are mandatory for a company
to appear in the scoped pool at all, depends on **company type** (operating, financial/bank,
pre-revenue, via the Sector/Lifecycle Router): each type has its own required set (no
fallbacks, no substitutes within that set) and its own full displayed set, typically larger
than the required set. No hero/tier visual split: every applicable metric renders the same
way, lens-grouped.

The *required* (eligibility) sets per type live in [`data_contract.md`](data_contract.md)'s
"Card eligibility" section. The *full displayed* set per type, typically larger than the
required set, isn't enumerated in any doc, including this one; `metrics_for_card()`
(`frontend/card_copy.py`) is the sole authoritative source, deliberately not duplicated into a
doc that would need to stay in sync with it (see [`ui/card_metric_cell.md`](ui/card_metric_cell.md)'s
"Metric stack" section for why). An earlier version of this section hardcoded a single "five
mandatory metrics" table that conflated the two concepts and fell out of sync with the app once
card content started varying by company type. It was left standing after the (correct,
`is_card_eligible`-level) five-metric picture stopped being the whole story for the growing
majority of cards.

**Live price** is not on the batch card (pipeline is not real-time). No on-card live-quote
widget in v1 — users open **Yahoo Finance** via the card footer link (`st.link_button`).

**Company context:** optional `business_summary` from Yahoo — word-limited preview on the card,
with its own inline Read more/Show less toggle when truncated (see
[`ui/disclosure_pattern.md`](ui/disclosure_pattern.md)) — not inside the learn panel.

**Health verdict + AI read (Slice 6c):** a 🟢/🟡/🔴 verdict (deterministic rules, Slice 5a) plus a
short Claude-written plain-language read (Slice 5b) render right after identity, always
visible — see the Progressive disclosure table below and
[`data_contract.md`](data_contract.md)'s `card_assessments` section. Omitted entirely (no
placeholder) when a card has no matching assessment yet.

**Large constituent bucket, smaller eligible pool:** index constituents are ingested broadly;
only tickers passing their company type's eligibility gate enter discovery. Bad or incomplete
data erodes trust.

---

## Progressive disclosure (card layout)

Three tiers — never all expanded at once on first load:

| Tier | Content | Goal |
|------|---------|------|
| **Scan** | Name, ticker, market, sector headline, health verdict badge, metric values for this company's type (lens-grouped, no hero/tier split) | Answer “what company?” in seconds |
| **Gloss** | AI read (always visible), sector one-liner, company blurb preview (expands inline to the full text when truncated), metric gloss lines under values | Plain-English context without clutter |
| **Deep** | “How we compare to similar companies” (median + benchmarks), “What do these metrics mean?” (each metric behind its own Read more toggle), practice-number playgrounds — all in **one** learn panel. The full company summary has its own inline toggle on the card face instead (Gloss tier), not in this panel | Optional learning on demand |

**Median primer and sector benchmarks** live inside **How we compare to similar companies**
(inside the one learn panel `st.expander`), not always visible. When fewer than 8 eligible
peers exist in the sector within that market, **hide benchmark UI entirely** — no orphan
“unavailable” line on the card face.

**Success check (mobile):** user can read company + sector + health verdict without scrolling,
with at least the first metric's value visible above the fold; Save remains reachable. (Not
re-verified against the current, larger per-type metric counts as part of this doc fix: a
"how many metric values fit above the fold now" check is a UX question, not a doc-accuracy
one; see [`ui/card_metric_cell.md`](ui/card_metric_cell.md)'s 480px smoke checklist.)

---

## Benchmarking (v1)

- Compare each metric to **sector median** within the **app universe** (same `market_code`).
- **One card-level median primer** inside the compare expand when benchmarks are available.
- **Recap list** (inside the compare expand): per-metric lines use short wording (e.g.
  **Above median** / **Below median**); sector name appears once in the sector header.
- **Card face**: a monochrome range mark instead of wording — this company's value
  positioned between its sector's min and max, median labeled. Same underlying policy
  (below), different mechanism; see [`ui/card_metric_cell.md`](ui/card_metric_cell.md).
- **No color coding on benchmarks in v1 (monochrome only)** — applies to both mechanisms.
- Show sector context: e.g. `Consumer Cyclical (42 companies)`.
- **Benchmark is not required for eligibility.** If sector median is unavailable (fewer than **8**
  eligible peers), **do not show** benchmark UI on the card — no warning line on the card face.
- Do not use naive “Top 10% in sector” rankings — misleading for debt, negative growth, etc.

---

## Discover: explore model (v2.4)

| Rule | Behavior |
|------|----------|
| Default scope | **All markets · All sectors** — not the full mixed worldwide queue |
| Filters | Market (registry markets or All), optional sector; client-side on exported mart |
| Walk | **Next company** advances within the filtered queue; the card meta line shows the card's own listing venue, then scope-aware position (e.g. `FTSE 100 · 3 of 47`): a company listed on more than one market in scope (Shell, Rio Tinto, Block Inc, ...) otherwise ships two cards a reader cannot tell apart; sector context stays on the card's own sector header, unchanged |
| Browse list | **Removed** — Discover is filter + walk only; use **Search** for intentional lookup |
| Cards per session | **No limit** |
| Ordering (walk) | Round-robin across markets in scope, unseen first, sector-balanced; queue **starts at US S&P 500** when that market is in scope (`HERO_MARKET_CODE`) |
| Universe | **Card-eligible tickers only** (per company type's eligibility gate) |
| Auth | **None in v1** — Save/Not now persist in browser localStorage on device |

### Save

**Meaning:** “I want to follow this company” (learning list).

- Adds ticker to **Saved**.
- Removes from scoped discover pool.
- Entry point for headlines and external research (Yahoo Finance link on card footer).

### Not now (Skip)

**Meaning:** “Not for me **right now**” — not “bad stock,” not permanent rejection.

- **Deprioritize** in scoped walk; ticker can resurface after many other cards.
- Always reachable via **Search**.

Neither action deletes pipeline data.

### Saved — return habit (learning list)

Saved is the home for **continue learning** on this device — not a spreadsheet or comparison grid.

| Pattern | v1 behavior |
|---------|-------------|
| **List** | Bordered rows: company name + ticker · sector (left-aligned); fundamentals as-of **once at tab top** — tap whole row (see [`ui/saved_list.md`](ui/saved_list.md)) |
| **Focus** | **One** Company Snapshot at a time — same layout as Discover |
| **Headlines** | Up to **3** recent headlines auto-load on focus (Yahoo via yfinance, session cache ~1 h); long titles use disclosure pattern |
| **Learn** | Shared “Understand these numbers” panel on the focused card |
| **Compare** | Optional later: **two** saved companies side-by-side in a **vertical** table — never horizontal N-column matrix on mobile |

**Out of scope for Saved v1:** metrics × N companies comparison matrix, selectbox + full card stacked
with a second navigation paradigm, horizontal scroll tables, headlines on Discover.

Filter default is **All markets · All sectors** — see [`explore_filters.py`](../frontend/explore_filters.py).

### Search (v1)

Intentional lookup by ticker or name. Same Company Snapshot layout if card-eligible.

---

## Education on the card

**Always visible (Tier 2 gloss):** one short plain-language line per metric under each value.

**On expand (Tier 3):** per-metric blocks — **analogy** always visible, then fuller
`METRIC_LEARN` copy behind its own Read more/Show less toggle — in “Understand these
numbers”; sector median context in “How we compare to similar companies.”
Optional interactive playgrounds follow the Kennzahlen-Schule pattern in
[`ux_principles_finanz_lern_apps.md`](ux_principles_finanz_lern_apps.md).

Keep copy concise. The card must remain scannable in under 30 seconds.

---

## UI component specs

Layout-level specs for agents and reviewers — ASCII wireframes, anti-patterns, 480px smoke checks:

| Spec | Covers |
|------|--------|
| [`ui/design_system.md`](ui/design_system.md) | Design tokens (spacing, radius, type scale), shared row/button primitives |
| [`ui/saved_list.md`](ui/saved_list.md) | Saved learning list rows, focus + headlines, freshness line |
| [`ui/discover_header.md`](ui/discover_header.md) | Brand → tagline → nav (+ ⋯ inline) → filters → stats |
| [`ui/card_metric_cell.md`](ui/card_metric_cell.md) | Label / value / gloss hierarchy, value-aware copy |
| [`ui/disclosure_pattern.md`](ui/disclosure_pattern.md) | Read more / Show less for long copy |

UX PRs that change these areas must cite the relevant spec in the PR body.

---

## Markets

Markets are **registry-driven** (`docs/market_registry.yml`), which is the list to read rather
than any count written into prose. Every market is added only after a **yfinance coverage audit**
confirms the operating-type eligibility metrics (the majority case for any market's constituents)
are obtainable for a meaningful share of its constituents. The audit is per market; whether
markets are branched one at a time or in batches is the owner's call and has been both.

Do not activate a market in the app until eligibility counts meet [`data_contract.md`](data_contract.md)
thresholds.

---

## Out of scope for v1

- Real-time or intraday price on the batch card
- ROIC (too complex to compute reliably from yfinance; may revisit in a later release)
- Metric fallbacks or substitute proxies when a primary field is missing
- Buy/sell recommendations or portfolio tracking
- Color-coded benchmark badges
- Dating-app interaction patterns or gamified streaks as core UX
- Auth / cross-device sync
- **News on Discover cards**
- Discover **browse list** expander (removed — walk + Search only)
- On-card **live quote** button (removed — Yahoo Finance footer link only)
- **Metric range filters** in Filters popover until mobile-friendly design (#109)

---

## Phase 2 backlog (stickiness + depth)

| Item | Status |
|------|--------|
| Saved-tab headlines (2–3 per company, on focus) | **Shipped** — on-demand yfinance, session cache; not a separate CI workflow |
| Discover metric range filters | **Backlog** — [`backlog/discover_metric_filters_phase2.md`](backlog/discover_metric_filters_phase2.md) |
| Richer saved-company updates when fundamentals refresh | Backlog |
| Optional **Not now** review list | Backlog |
| Optional filter persistence to localStorage | Backlog |
| Two-company saved compare (vertical table) | Backlog |
