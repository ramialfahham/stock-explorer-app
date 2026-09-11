---
name: onboard-market
description: Add or activate a stock market index (CAC 40, OBX, TSX 60, FTSE MIB) in this app's ingestion universe. Use when asked to add, onboard, activate or enable a market or index, or to flip ingest_active in docs/market_registry.yml. Do NOT use for anything else the word "market" appears in: market cap, market_code, sector or market benchmarks, or the metric catalogue.
---

# Onboarding a market

## Follow the checklist. Do not improvise one.

**`docs/data_contract.md`, "Market activation checklist".** It is the only copy and it is the
whole procedure. Read it before doing anything.

France was onboarded without reading it: three of the seven steps it had then were done and
four skipped. One of the skipped ones would have aborted the next scheduled export for **every**
market, not just the new one, with every CI check green. The checklist has since been corrected
and extended, and it explains that failure where it belongs, at the step concerned. The reason to
read it is that improvising it has already failed once.

## Two traps the checklist cannot tell you

**Wikipedia returns 403 to pandas' default user agent.** Fetch through
`ingestion.constituents.refresh`, never `pandas.read_html` on a bare URL. The repo's fetcher
sets a user agent for exactly this reason.

**`table_index` is positional, and silently wrong rather than loud.** `refresh.py` raises only
when the index is out of range; an index that is wrong but still in range returns a different
table with no error. Find it by scanning for a table whose columns include Ticker or Symbol, and
record the row count so a later mismatch is visible.

## Before starting, tell the owner what it costs

A market is permanent load, not a one-off change: 20 to 60 more tickers ingested on every run,
plus one Claude Haiku call per eligible card whenever that card's inputs change. For scale, the
last five-market run took 73 minutes at 921 cards against a 2 hour CI timeout. Four markets
have been activated since and none has run: France, Netherlands, Switzerland and Spain add 120
tickers to that, projecting roughly 101 more cards. Both halves of this go stale: read the run
history in `.claude/active_work.md` for what has actually run, and `docs/market_registry.yml`
for what is active. This sentence is a starting figure, not a current one.

## What is the owner's call

- **Which markets**, and in what order.
- **Which index**, where a country has more than one credible choice. Norway was OBX rather than
  the broader OSEBX. Present the options and recommend; do not pick silently.
- **Currency display** for a currency not already in `_CURRENCY_SYMBOLS`. The rule and the
  reasoning sit beside that constant in `scripts/assessment_rules.py`, mirrored in
  `frontend/card_copy.py`: use each currency's real-world form, not a uniform one. Both copies
  must change together; `test_currency_symbol_maps_are_mirrors` catches a single-copy edit.

A thin or stubbed constituent is NOT an owner decision: carry it and let eligibility drop it.
Silently excluding a real index member to make a count look clean is the worse error.
