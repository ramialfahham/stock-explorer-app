# Name-vs-yfinance audit guard

**Status:** Backlog. Flagged three times (Nikkei, SMI, Block ticker fixes, 2026-08-28/29),
never built. Scoped as its own item 2026-08-29.

## Summary

An automated check that compares every active market's seed `company_name` against yfinance's
`info_long_name` for the same ticker, and flags a real divergence, instead of relying on a
manual audit each time a name-quality defect surfaces.

## Context

Three name/ticker-quality defects were found and fixed by hand this session: eleven wrong
`jp_nikkei225` company names, the `ch_smi` legal-name register (nineteen names), and
`au_asx200`'s wrong Block ticker. All three were found the same way: a one-off script fetching
yfinance and diffing it against the seed, run because someone happened to look.

The two existing guards in `tests/ingestion/test_market_onboarding.py`
(`KNOWN_CROSS_MARKET_COMPANIES`, the duplicate-headline detection) only catch a wrong name when
the *true* company also happens to be a separate row in the same seed with a near-identical
headline, a collision. For the Nikkei audit, that caught exactly 2 of the 11 wrong names
(the ones where the seed's actual owner was also present as another row); the other 9 had no
colliding row anywhere in the seed and looked correct to every check that already existed.

## Open questions (owner decisions, not answered here)

- **Live fetch vs cached snapshot.** A live yfinance call inside CI is a network dependency,
  subject to rate limits and flakiness, on every run. A periodically-refreshed cached snapshot
  avoids that but needs its own refresh cadence and staleness story.
- **Fuzzy-match tolerance.** Exact string equality would fail on harmless stylistic differences
  ("Nestlé SA" vs "Nestlé S.A.", "Alcon Inc" vs "Alcon Inc.") that are not defects. A real
  defect ("Novartis International AG" vs "Novartis AG") needs to fail. Where that line sits is
  a genuine design question, not a small tuning knob.
- **Scope.** Every active market's every row, or only markets whose `docs/constituent_sources.yml`
  entry has `provider: wikipedia`? `jp_nikkei225` is `provider: manual` (no stable public
  Wikipedia table, hand-curated via `scripts/import_constituents.py`), so it may need different
  treatment than a scraped market.
- **Failure mode.** Hard-fail CI on any PR touching a seed (blocking), or a warning-only report
  a human reviews on a schedule? A hard fail risks blocking unrelated PRs on a pre-existing,
  unfixed defect; a report-only guard risks being ignored the way the manual audits were, until
  someone happened to look.
- **New mechanism.** Whichever shape this takes is a new CI step, and per the working
  agreement's decision-rights section, a new mechanism (new dependency, service, or workflow
  step) is an owner call, not something to add unilaterally when this item is picked up.
- **Tickers, not just names.** The Block ticker defect was a wrong *ticker*, not a wrong name;
  `ingestion/constituents/ticker_overrides.csv` already exists as the correction mechanism for
  that case. A parallel guard ("does `{ticker}{exchange_suffix}` resolve on yfinance at all")
  is a related but distinct check from the name comparison this doc scopes, and may be a
  separate backlog item rather than folded into this one.

## Draft acceptance criteria (needs owner confirmation before building)

- Compares every in-scope market's seed `company_name` against yfinance's `info_long_name` for
  the matching ticker.
- Flags a real divergence; passes on a stylistic-only difference (legal-form suffix, punctuation,
  diacritics).
- Runs on an agreed cadence, decided alongside the live-fetch-vs-cached-snapshot question above.
- Would have caught, or at minimum flagged for review: all eleven Nikkei defects, the SMI
  legal-name register question (not necessarily the exact trade-name choice, which is a naming
  decision this guard cannot make, but the fact that the seed's register differs from
  yfinance's).

## Related

- `tests/ingestion/test_market_onboarding.py`: `KNOWN_CROSS_MARKET_COMPANIES`, the existing
  collision-based guard this would supplement, not replace.
- `dbt_analytics/seeds/company_name_overrides.csv`: where a confirmed name defect gets
  corrected once found, built for the Nikkei fix and reused for SMI.
- `ingestion/constituents/ticker_overrides.csv`: the parallel load-time correction mechanism
  for a wrong ticker, built for the Block ticker fix.
- Prior manual audits this session: `jp_nikkei225` (2026-08-28), `ch_smi` (2026-08-28),
  `au_asx200` Block ticker (2026-08-29).
