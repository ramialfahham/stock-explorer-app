# North star — Stock Swipe App

Product vision and UX principles. When implementation choices conflict, this document wins
for user-facing behavior. Technical contracts live in [`data_contract.md`](data_contract.md).

---

## What we are building

A **card-based stock discovery app** for **finance-curious beginners** — people with near-zero
prior knowledge who want to **learn and discover** companies, not execute trades.

Each card is an **analyst-grade snapshot at low barrier**: five fundamental metrics, plain
language, optional depth. Sessions are **quick scans** with room to go deeper when curious.

**Not investment advice.** Metrics are informational. The app educates; it does not recommend
buys or sells.

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
| 4 | Net debt / EBITDA | — | Scroll / expand |
| 5 | FCF margin | — | Scroll / expand |

**Live price** is not on the batch card (pipeline is not real-time). Optional **on-demand**
quote via yfinance in Streamlit is acceptable if low effort. An external Yahoo Finance link
is always fine.

**Large constituent bucket, smaller eligible pool:** index constituents are ingested broadly;
only tickers passing the five-metric gate enter discovery. Bad or incomplete data erodes trust.

---

## Benchmarking (v1)

- Compare each metric to **sector median** within the **app universe** (same `market_code`).
- **Direction-aware wording** in the UI (e.g. lower debt vs median is favorable; higher EBIT margin is
  favorable). **No color coding** on benchmarks in v1 — monochrome text only.
- Show sector context: e.g. `Technology (47 companies)`.
- **Benchmark is not required for eligibility.** If sector median is unavailable (too few peers,
  default threshold: fewer than **8** companies in sector within that market), the card still
  shows all five metrics and omits the comparison line with copy such as:
  `Comparison unavailable (small sector)`.
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

### Save

**Meaning:** “I want to follow this company.”

- Adds ticker to **Saved** (watchlist).
- Removes from discovery queue (or lowest priority).
- Entry point for optional on-demand quote and external research links.
- Optional micro-education after save (e.g. why operating margin matters) — never blocking.

### Skip

**Meaning:** “Not for me **right now**” — not “bad stock,” not permanent rejection.

- **Deprioritize** in queue; ticker can resurface after many other cards.
- Always reachable via **Search** (ticker or company name).
- Optional **Skipped** review list in a later release.

Neither action deletes pipeline data.

### Search (v1 or early v2)

Intentional lookup by ticker or name. Same card layout if the company is card-eligible.

---

## Education on the card

**Always visible:** one short plain-language line per metric (what it is, not how to trade).

**On expand / Learn:** 2–3 sentences plus optional link to an external explainer.

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

---

## Phase 2 (stickiness, separate from fundamentals)

- **News** feed (daily refresh) — optional habit layer, not mixed into fundamentals CI gates
- Richer saved-company updates when fundamentals refresh weekly
