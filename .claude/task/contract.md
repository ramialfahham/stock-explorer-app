# Task contract
> DISPOSABLE. **Owns:** THIS task's objective, `scope_paths`, reserved decisions and
> `done_when`.
> **Never:** anything that outlives the task. Overwritten by the next task.

objective: Closes #47 (MR 2 of 2; MR 1 is !248, merged) -- findings 20 and 30. One company-identity
  rule in the display layer, keyed on the resolved Yahoo symbol and applied to the All-markets
  list, its sector options and search, and a deck fetch that pages by the `current_cards` view's
  unique key with no Python dedupe. Finding 33 stays as documented, no edit.

scope_paths:
  - frontend/explore_filters.py
  - frontend/app.py
  - frontend/supabase_cards.py
  - tests/frontend/test_explore_filters.py
  - tests/frontend/test_supabase_cards.py
  - tests/frontend/test_app.py
  - tests/ingestion/test_market_onboarding.py
  - tests/tooling/test_quality_audit.py
  - docs/data_contract.md
  - docs/north_star.md
  - docs/quality_criteria.json
  - .claude/active_work.md
  - .claude/task/contract.md
  - .claude/task/review.md

decisions_reserved: delegated to the agent by the owner in-thread, in the owner's words "I have
  no idea. You should act as the expert." and then "go", each call stated with its reason before.
  Finding 20: the rule stays in the display layer (the owner's decision in issue #7), not moved
  upstream. A company's identity is its resolved Yahoo symbol (`yfinance_symbol`), not the bare
  card ticker: round-1 review showed the bare ticker merges unrelated companies (28 bare-ticker
  collisions across the seeds, 24 of them unrelated, for example Merck & Co. and Merck KGaA,
  AT&T and Telus, Boeing and BAE Systems), which the All-markets dedupe on main already does.
  This ends that merge: the 24 unrelated pairs (Merck & Co. and Merck KGaA, AT&T and Telus,
  Boeing and BAE Systems, others) each show two cards in All markets again. Five same-company
  pairs that main merges by accident become two cards: Newmont, Rio Tinto, ResMed, Block (`XYZ`
  in the S&P 500 and `XYZ.AX` on the ASX, after the ticker override) and News Corp's Class B pair
  (NWS, NWS.AX); its Class A card NWSA is unchanged. The later snapshot wins; a tie goes to the
  market listed first in `MARKET_DISPLAY_NAMES`, so with equal snapshot_dates Airbus shows as DAX
  and ArcelorMittal's MT.AS as CAC 40; the winner sets the card's market label and
  sector peer group, so the tie-break can decide whether the sector comparison shows. Dedupe runs
  before the sector and preset filters, so a company is judged by its latest listing, and the
  sector options follow the same rule. Saved state stays per listing (Saved tab, cookie,
  single-market filters unchanged); All markets lists companies, so it hides a company when any
  of its current listings is saved. Search lists a same-listing company once. Round-1 and round-2
  scope widening under the grep-the-claim rule: `tests/ingestion/test_market_onboarding.py`
  (three display sentences made false, and the suffix test now compares values to the registry),
  `docs/north_star.md` (the Save reversibility sentence is false in All markets while a second
  listing stays saved). Finding 30: the deck-level dedupe is dropped and the deck pages by
  (market_code, ticker); the single-card dedupe and its business_summary backfill stay.
  The owner's own answer, given after being asked: criterion FE-1 names deduplication as logic
  the frontend must not compute, which this rule contradicts; the owner chose "A", record the
  exception and keep the rule in the display layer. Recorded as criteria version 2
  (`docs/quality_criteria.json` FE-1, with its fingerprint in `tests/tooling/test_quality_audit.py`).

done_when:
  - All markets returns the same Airbus listing (`de_dax`) for either deck order at an equal
    snapshot_date (`test_dual_index_tie_resolves_to_the_same_market_in_either_deck_order`).
  - Saved is per listing: All markets hides Airbus when either listing is saved, the DAX filter
    still lists it, the CAC 40 filter hides the saved one, and a saved listing no longer in the
    deck hides nothing (`test_all_markets_hides_a_company_when_either_listing_is_saved`,
    `test_all_markets_ignores_a_saved_listing_that_left_the_deck`).
  - Companies sharing a bare ticker stay two (MRK in `us_sp500` and `de_dax`, T in `us_sp500`
    and `ca_tsx60`) in the list, under a save, and in search
    (`test_all_markets_keeps_two_companies_that_share_a_bare_ticker`,
    `test_search_matches_keeps_two_companies_that_share_a_bare_ticker`).
  - A company follows its latest listing through the sector filter, a metric preset and the
    sector options (`test_all_markets_judges_a_company_by_its_latest_listing_before_the_sector_filter`,
    `..._before_a_metric_preset`, `test_sectors_for_market_all_markets_skips_a_sector_held_only_by_a_losing_listing`).
  - `app._search_matches` returns a same-listing company once, for either deck order
    (`test_search_matches_lists_a_company_in_two_indices_once`).
  - `fetch_deck` sorts by `market_code` then `ticker` and applies no dedupe of its own: two
    snapshots of one key come back as served (`test_fetch_deck_pages_by_the_views_unique_key`,
    `test_fetch_deck_returns_the_views_rows_as_served`).
  - Each new test fails when its production change is reverted: the author ran six mutations
    (bare ticker as key, saved check by listing only, tie-break removed, dedupe after the
    filters, sector options not deduped, dedupe put back in `fetch_deck`) and each is caught.
  - `_EXCHANGE_SUFFIX` equals the registry's `exchange_suffix` for every active market
    (`test_every_active_market_is_named_and_suffixed_in_the_frontend`).
  - `docs/quality_criteria.json` is version 2 and its fingerprint test passes.
  - `git grep -n -e fetch_deck_rows -e dedupe_by_ticker -e _company_key -- frontend tests docs`
    prints nothing.
  - `git grep -n -e "once per market it belongs to" -e "shows it twice" -e "Issue #7 covers the display fix" -- docs tests`
    prints nothing; `docs/data_contract.md` states the resolved-symbol rule.
  - `git grep -n -i "reserved and unbuilt" -- .claude/active_work.md` prints nothing.
  - `.claude/active_work.md` stays under 32000 bytes (its budget test passes).
  - `pytest tests` and `python scripts/bootstrap.py --verify` pass.

known_limits:
  - A company on two venues resolves to two symbols and is two cards (Shell, Unilever,
    ArcelorMittal's MTS.MC, Newmont, News Corp, Rio Tinto, ResMed, Block). The upstream
    name-level guard lives only in the onboarding test.
  - Which market "owns" a same-listing company is arbitrary but stable (the dict order of
    `MARKET_DISPLAY_NAMES`, pinned only by the Airbus pair), not a home-market rule; a home-market
    rule needs data upstream and is the owner's product call. Because the winner sets the sector
    peer group, it can decide whether a beginner sees the sector comparison at all.
  - Saved state is per listing, so the two listings of one company behave independently outside
    All markets: saving the CAC 40 listing leaves the DAX listing in the DAX filter, and saving
    there adds a second Saved row. Search shows the winning listing only and has no saved
    exclusion (search showed both listings before).
  - The identity key is not upper-cased and rests on `_EXCHANGE_SUFFIX` in
    `frontend/live_quote.py`, a module whose docstring covers Yahoo symbols and URLs; a test pins
    its values to the registry. A market missing from the map would resolve with an empty suffix.
  - "The latest snapshot decides" holds among eligible listings only (the deck and the filters
    drop ineligible rows first): a company whose newest listing is ineligible and whose other
    listing is eligible and older shows the older one. Main behaves the same way.
  - The sort-key claim rests on Postgres documenting LIMIT/OFFSET over a non-unique ORDER BY as
    unspecified; per-(market_code, ticker) uniqueness rests on the `current_cards` DISTINCT ON,
    with no CI coverage of the SQL, only the fake-client call log.
  - Present since round 1, filed as follow-ups: `docs/constituent_sources.yml` and one
    `test_market_onboarding.py` docstring say a dual-index company "ships two cards" (true of
    deck rows); `frontend/live_quote.py`'s docstring omits the identity use; migration 020's
    comment says "each company's newest row" (per listing; an applied migration, not edited).

regression_checklist:
  - A single-market filter lists every eligible row of that market except the saved listing, as
    before (exclusion by (market_code, ticker)).
  - The Saved tab is unchanged: it matches saved (market_code, ticker) keys exactly.
  - `dedupe_to_latest_snapshot` (the single-card path) still backfills business_summary from the
    older snapshot and resolves a same-market tie to the first row, as before.
  - `DECK_COLUMNS` and the deck's selected columns are unchanged.
