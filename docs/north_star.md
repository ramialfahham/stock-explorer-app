# North star — Stock Explorer

Product vision and UX principles. When implementation choices conflict, this document wins
for user-facing behavior. Technical contracts live in [`data_contract.md`](data_contract.md).

**Product name:** **Stock Explorer** (in-app and docs). Repo name may remain `stock-swipe-app`.

---

## What we are building

A **card-based stock discovery app** for **finance-curious beginners** — people with near-zero
prior knowledge who want to **learn and discover** companies, not execute trades.

Each card is an **analyst-grade snapshot at low barrier**: five fundamental metrics, plain
language, optional depth. Sessions are **quick scans** with room to go deeper when curious.

**Not investment advice.** Metrics are informational. The app educates; it does not recommend
buys or sells.

**Interaction model:** browse with **Save** and **Skip** — not swipe gestures or dating-app
patterns.

---

## Audience and tone

| Dimension | Choice |
|-----------|--------|
| Audience | Beginners — assume no finance vocabulary |
| Motivation | Learn + discover; build a daily browsing habit over time |
| Tone | Fun but serious; education integrated, never gimmicky |
| Builder lens | Dashboard-like reduced overview; v1 optimizes for beginners |

Use **“card session”**, **“save”**, **“skip”**, **“not interested right now”**. Do not use
dating-app metaphors in product copy or documentation.

---

## The card — five mandatory metrics

Discovery cards show **fundamentals**, not batch pipeline prices. A company appears in the
discovery queue only when **all five** metrics are present (no fallbacks, no substitutes).

| # | Metric | Role on card | Deep dive |
|---|--------|--------------|-----------|
| 1 | Forward P/E | Valuation — visible | — |
| 2 | EBIT margin | Quality / profitability — visible | — |
| 3 | Revenue growth YoY | Momentum — visible | — |
| 4 | Net debt / EBITDA | — | Visible on card (below hero three) |
| 5 | FCF margin | — | Visible on card (below hero three) |

**Live price** is not on the batch card (pipeline is not real-time). **On-demand** quote via
yfinance on button tap is acceptable (session-cached, not in mart). An external Yahoo Finance
link is always available on the card footer.

**Company context:** optional `longBusinessSummary` from Yahoo — truncated preview on the card;
full text in an expand panel when present.

**Large constituent bucket, smaller eligible pool:** index constituents are ingested broadly;
only tickers passing the five-metric gate enter discovery. Bad or incomplete data erodes trust.

---

## Progressive disclosure (card layout)

Three tiers — never all expanded at once on first load:

| Tier | Content | Goal |
|------|---------|------|
| **Scan** | Name, ticker, market, sector headline, five metric values | Answer “what company?” in seconds |
| **Gloss** | Sector one-liner, company blurb preview, metric gloss lines, median primer | Plain-English context without clutter |
| **Deep** | “What do these metrics mean?” panel, “About this company” full summary | Optional learning on demand |

**Success check (mobile):** user can read company + sector + three hero metrics without scrolling;
Save remains reachable.

---

## Benchmarking (v1)

- Compare each metric to **sector median** within the **app universe** (same `market_code`).
- **One card-level median primer** when benchmarks are available (defines “median” once).
- Per-metric lines use short wording (e.g. **Above median** / **Below median**); sector name
  appears once in the sector header.
- **Direction-aware wording** — no color coding on benchmarks in v1 (monochrome text only).
- Show sector context: e.g. `Consumer Cyclical (42 companies)`.
- **Benchmark is not required for eligibility.** If sector median is unavailable (fewer than **8**
  eligible peers in sector within that market), show once:
  `Comparison unavailable (small sector)` — no per-metric benchmark lines.
- Do not use naive “Top 10% in sector” rankings — misleading for debt, negative growth, etc.

---

## Session and queue

| Rule | Behavior |
|------|----------|
| Cards per session | **No limit** |
| Markets | **Mixed by default**; `market_code` visible on each card |
| Ordering | **Not random** — round-robin across markets, unseen first, sector-balanced |
| Universe | **Card-eligible tickers only** (all five metrics) |
| Not analyst picks | No “famous brands only” or buy-list curation |
| Auth | **None in v1** — Save/Skip persist in browser localStorage on device |

### Save

**Meaning:** “I want to follow this company.”

- Adds ticker to **Saved** (watchlist).
- Removes from discovery queue (or lowest priority).
- Entry point for optional on-demand quote and external research links.

### Skip

**Meaning:** “Not for me **right now**” — not “bad stock,” not permanent rejection.

- **Deprioritize** in queue; ticker can resurface after many other cards.
- Always reachable via **Search** (ticker or company name).

Neither action deletes pipeline data.

### Search (v1)

Intentional lookup by ticker or name. Same card layout if the company is card-eligible.

---

## Education on the card

**Always visible (Tier 2 gloss):** one short plain-language line per metric under each value.

**On expand (Tier 3):** fuller `METRIC_LEARN` copy in a single “What do these metrics mean?”
panel — not five separate popovers.

Keep copy concise. The card must remain scannable in under 30 seconds.

---

## Markets

Markets are **registry-driven** (`docs/market_registry.yml`). v1 includes US, UK, JP, AU, and
**DAX (Germany)**. Additional European indices are added **one at a time** after a **yfinance
coverage audit** confirms all five metrics are obtainable for a meaningful share of constituents.

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

---

## Phase 2 (stickiness, separate from fundamentals)

- **News** feed (daily refresh) — optional habit layer, not mixed into fundamentals CI gates
- Richer saved-company updates when fundamentals refresh weekly
- Optional **Skipped** review list
