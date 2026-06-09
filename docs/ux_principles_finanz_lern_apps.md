# UX principles for finance learning apps

Supplementary pedagogy reference for Stock Explorer. Original research (German):
[UX-Prinzipien für Finanz-Lern-Apps](https://docs.google.com/document/d/1iy3_5qxfiJpskdIeIYLauE2c8Kfxuoa0ot92ZGNONiI/edit).

When this document conflicts with [`north_star.md`](north_star.md) on product behavior, **north_star wins**
(metric set, Save/Not now model, no auth in v1).

---

## Core principles (applied to Stock Explorer)

### Progressive disclosure

Present scan-friendly KPIs first. Definitions, formulas, analogies, and sector comparisons stay
behind explicit user action (expand, tab, or tap) — not on first paint.

### Active user paradox

Beginners skip long tutorials. Learning happens through **safe interaction**: hypothetical
scenarios, playgrounds, and micro-checks tied to real company data — not static walls of text.

### Bloomberg principle (responsible density)

Do not hide data behind oversimplification. Structure it for **legibility at a glance**:
whitespace, typography hierarchy, grouped cards. Comparison tables are valid only when readable
on mobile without horizontal scroll.

### Neutral palette

Dark editorial base; gold accent for actions. Avoid red/green as “good stock / bad stock” signals.
Benchmarks use monochrome directional text (↑/↓/→) per north_star.

### Friction as feature (education only)

Short reflective pauses before quiz feedback are OK. Do not add friction to navigation (Save,
tab switches, opening a saved company).

### Consistency

One tab = one primary layout. Do not stack matrix + selectbox + duplicate full card on Saved.

### Gamification tied to cognition

No streaks, XP, or leaderboards in v1. Optional “understood this metric” checks on device are OK.

### Streamlit constraints

- Prefer `st.number_input` over high-cardinality sliders
- Cache expensive fetches (`@st.cache_data`)
- Stable widget keys per ticker + context prefix
- Set `st.set_page_config` first to avoid layout jump

---

## Kennzahlen-Schule pattern (metric school)

For each of the five fundamentals:

1. **Analogy** — one beginner metaphor (doc: “Amortisationszeit” for P/E)
2. **Definition** — short plain-language explanation (`METRIC_LEARN`)
3. **Playground** — low-cardinality inputs; hypothetical numbers only
4. **Micro-check** — one radio question using **this company’s** exported values; neutral feedback

Port **patterns** onto Stock Explorer’s five metrics (forward P/E, operating margin, revenue
growth YoY, net debt/EBITDA, FCF margin) — do not swap to EPS/KGV/KBV/ROE/D/E from the doc examples.

| Stock Explorer metric | Doc analogue | Analogy direction |
|----------------------|--------------|-----------------|
| Forward P/E | KGV | Years of expected earnings priced into the share |
| Operating margin | Profitability | Share of each sales dollar kept as operating profit |
| Rev growth YoY | Momentum | Growing, flat, or shrinking vs one year ago |
| Net debt / EBITDA | D/E / solvency | Years of operating profit to repay net debt |
| FCF margin | Cash quality | Cash left after running the business |

---

## Saved tab (learning list)

Per north_star and this doc:

- **Vertical list** of saved companies (name, ticker, sector, freshness)
- **Single focus** — one Company Snapshot at a time when a row is opened
- **No** horizontal N-column comparison matrix in v1
- Optional later: compare **two** saved companies in a vertical 5×2 table (mobile width)

Phase 2 stickiness: 2–3 headlines per saved company on Saved tab only — separate from fundamentals CI.

---

## Discover default scope (doc alignment)

- **Filter default:** All markets · All sectors (north_star v2.3)
- **Walk ordering:** US S&P 500 first when “Surprise me worldwide” is off (`HERO_MARKET_CODE`)
- Roadmap “default S&P 500” refers to walk bias, not hiding other markets from filters

---

## UX PR gate (see also working_agreement.md)

Before merging user-facing UX changes:

- [ ] Matches north_star tab behavior
- [ ] Matches component specs in [`docs/ui/`](ui/) when touching Saved, Discover chrome, or card metrics
- [ ] Mobile 480px smoke — one primary action visible; no horizontal scroll on Saved
- [ ] PR description states one-sentence user job (e.g. “Saved: continue learning company X”)
- [ ] ASCII or wireframe in PR body for new layout patterns
