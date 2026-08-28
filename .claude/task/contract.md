# Task contract

objective: Onboard Netherlands (AEX), Switzerland (SMI) and Spain (IBEX 35), the three queued
  markets that already had registry entries. Second of three batches; the owner chose batching
  by group over one branch per market. Every step of the activation checklist in
  `docs/data_contract.md` was followed, in order, using the `onboard-market` skill.

scope_paths:
  - docs/market_registry.yml
  - docs/constituent_sources.yml
  - docs/operations_guide.md
  - dbt_analytics/dbt_project.yml
  - storage/seeds/nl_aex/constituents.csv
  - storage/seeds/ch_smi/constituents.csv
  - storage/seeds/es_ibex35/constituents.csv
  - supabase/migrations/015_nl_ch_es_markets.sql
  - scripts/eligibility_baseline.ci.json
  - frontend/markets.py
  - frontend/live_quote.py
  - tests/ingestion/test_market_onboarding.py
  - tests/ingestion/test_constituent_seeds.py
  - ingestion/constituents/seeds.py
  - frontend/overflow_menu.py
  - frontend/card_copy.py
  - scripts/assessment_rules.py
  - dbt_analytics/models/4_intermediate/int_stock__card_metrics.sql
  - docs/supabase_setup.md
  - .claude/skills/onboard-market/SKILL.md
  - tests/frontend/test_overflow_menu.py
  - tests/tooling/test_assessment_rules.py
  - docs/north_star.md
  - docs/data_contract.md
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/active_work.md

# Which of the paths above were NOT in the original scope, and why each was added. Prose rather
# than a second list, because a list here duplicates `scope_paths` and the last one drifted out
# of agreement with it. The task artefacts and the three markets' own files were in scope from
# the start.
scope_widened:
  - Paths were added over four review rounds, all for the same reason: activating a
    ninth market and a sixth currency falsified sentences written when there were five of each,
    and leaving them is the "sweep stale prose on a semantic change" failure this branch has
    already been caught by twice. `scripts/assessment_rules.py`, `frontend/card_copy.py` and
    `int_stock__card_metrics.sql` are comment-only edits to the two `_CURRENCY_SYMBOLS` copies
    and the model that explains the 0.1% ratio test. `docs/north_star.md` still described a
    five-market v1 added "one at a time", which the owner's batching decision supersedes.
    `docs/supabase_setup.md` and `.claude/skills/onboard-market/SKILL.md` are the same class,
    caught a round later: the migrations table enumerated the files on disk, and the skill
    carried the only durable copy of the unrun-ticker cost, which this branch tripled.
    `tests/tooling/test_assessment_rules.py` holds the currency deny-list inventory, which a
    sixth currency falsifies, and `docs/data_contract.md` carries both the activation checklist
    this branch follows and the expansion rule the owner's batching decision supersedes.
    `frontend/overflow_menu.py`, `frontend/markets.py`, `tests/frontend/test_overflow_menu.py`
    and `tests/ingestion/test_constituent_seeds.py` are the genuine code changes and are argued
    in `done_when`.

impact_map:
  - 80 seed rows enter the ingestion universe: 25 Dutch, 20 Swiss, 35 Spanish. They are 80
    tickers but not 80 companies. `MT.AS` (ArcelorMittal) is already ingested under `fr_cac40`,
    so 79 new SYMBOLS ingest. Six of the 80 rows are companies the deck already has: `MTS.MC`
    (ArcelorMittal's Madrid line), `SHELL.AS` (Shell, already `SHEL.L`), `UNA.AS` (Unilever,
    already `ULVR.L`), `REN.AS` (RELX, already `REL.L`), `IAG.MC` (International Airlines Group,
    already `IAG.L`) and the `nl_aex` copy of `MT.AS`. **74 distinct companies are new**, and
    five companies gain a duplicate card: ArcelorMittal reaches three, the other four reach two.
    An earlier draft said 78 and named ArcelorMittal as the only case, because the collision
    guard is keyed on the resolved Yahoo symbol and a company listed on two venues resolves to
    two symbols. `test_no_unrecorded_company_appears_under_two_markets` now catches that class.
  - Sample audits project roughly 20, 19 and 26 card-eligible respectively, so the deck grows by
    about 65 cards on top of France's roughly 36. Cards, not companies: up to five of those are
    a second card for a company already in the deck.
  - Ingestion grows by 80 tickers per run and the read cost by one Haiku call per eligible card
    whenever its inputs change. The last five-market run was 73 minutes at 921 cards against a
    2 hour CI timeout; France and these three have not run.
  - `public.markets` gains three rows via migration 015. No schema change of any kind.
  - The market filter gains AEX, SMI and IBEX 35, live at merge, since it renders from a static
    map rather than the pipeline.
  - **CHF becomes user-visible on the next run, in the read prose.** An earlier draft of this
    contract said it did not, on the grounds that all three `currency_compact` metrics are
    `pre_revenue`-gated so no Swiss card renders a money amount. That is true and it is not the
    whole path: `build_read_messages` injects `Currency this company trades in: CHF` into every
    read prompt via `_display_currency`, which returns the bare code for an unmapped
    currency, and the comment at `:460` calls that line the only route by which currency reaches
    the model on operating and financial cards. Stated precisely, because an earlier draft
    overstated it: nothing ships at merge, since no Swiss card or read exists until the next
    production run. On that run, roughly 19 Swiss reads will be generated from a prompt carrying
    `CHF`, and any read that phrases a margin per unit of currency will print it. The grounds
    for deferring were wrong; the question is escalated instead.
  - **No Swiss card is expected to render a money amount**, since all three `currency_compact`
    metrics are `pre_revenue`-gated and an SMI constituent classified `pre_revenue` would be
    surprising. Expected, not verified: the market has never run. The fallback is safe either
    way, rendering `CHF 2.1B` rather than a wrong symbol.
  - **Sector peer comparison for the new markets is uncertain, not absent.** The threshold is
    `{% set peer_threshold = 8 %}`, and `int_stock__sector_benchmarks.sql` groups by
    `(market_code, sector)`, so peers are
    counted within a market. Counting the Spanish seed by likely Yahoo sector puts Financial
    Services, Utilities and Industrials each at about 7 before the eligibility filter. The
    benchmark CTE counts only card-eligible, non-pre-revenue rows, so the eligible count can only
    be at or below the seed count, so a sector at 7 in the seed cannot reach a gate of 8 and its
    comparison stays hidden, which is the safe direction. That sentence is about the eligible-versus
    -seed relation and holds for any sector; what is NOT settled is which sectors sit at 7 in the
    seed. Industrials is "about 7" on the same uncertainty, with Acciona SA and Indra as the
    candidate eighths. **Utilities is where it matters, because it is the one whose eighth row
    would make the peer set non-independent**: it is 7 without Acciona SA and 8 with it, so if
    Yahoo files Acciona
    SA under Utilities the medians would unlock for every Spanish Utilities card, over a peer set
    of 8 rows holding a consolidated parent and subsidiary. Would, not will: all 8 still have to
    clear `is_card_eligible`, and the ES sample estimate is 75%. See the issue #7 bullet. An earlier
    draft asserted "the largest is Spanish utilities at 5":
    that number was not derived from anything, the seeds carry no sector column, and these
    markets have never run. What IS certain from the grouping is the thing that matters for
    safety: adding markets cannot move any existing market's peer counts or medians, so no
    already-shipped number changes.
    Switzerland is the one case that is not uncertain: with 20 constituents its largest plausible
    sector is about 5, so no SMI card can carry a sector median or range at a gate of 8. The card
    degrades gracefully and says so, which is the safe direction, but it means the whole market
    ships without peer context.

decisions_reserved:
  - **ANSWERED 2026-08-28. The 20-card warn threshold is wrong and the owner has said so.** It
    compares an absolute card count against an index that has only 20 members, so Switzerland
    clears it only by having every single constituent card-eligible. Strictly 20 of 20 does pass,
    since the comparison is `<`, but a bar only perfection clears carries no information. Not
    changed on
    this branch: it is a CI gate, changing it here is the "weaken the gate that fails your work"
    move the France branch was pulled up for, and the fix wants its own contract. Filed for
    phase 2, where the eligibility work already sits. Switzerland warns until then.
  - **ANSWERED 2026-08-28. Currency rendering follows real-world practice, per currency.** The
    owner's rule: use the form a reader would actually meet. That confirms the current behaviour
    for CHF, which IS written "CHF" in practice, so nothing on this branch changes. It also
    settles the queue: `CAD -> C$`, and SEK, DKK and NOK as ISO codes rather than "kr", because
    "kr" names three different currencies and this app puts markets side by side.
  - **ANSWERED 2026-08-28. Seed names get corrected in a dbt model, not by hand.** The owner
    directs that the name mapping become a dbt model, with the correction applied in it,
    following the pattern used in the football-data project. The layer detail is below. That
    is a new mechanism and its own piece of work, filed separately. It covers the NAME defects:
    the SMI legal names and the eleven wrong Nikkei names become mapping rows rather than CSV
    edits, because `company_name` is only ever consumed downstream, through `dim_stock`'s
    coalesce. Switzerland ships with legal-name headlines until that lands.
    **The Block ticker is NOT fixed by this and must not be folded into it.** A wrong TICKER is
    upstream of dbt entirely: `ingestion/yfinance/ingest.py:309` calls `load_constituents`, which
    reads the CSV, and line 312 builds the fetch list from its `ticker` column, which lines 313 and
    314 hand to the price and fundamentals fetchers. CI runs
    ingestion before `dbt build`, and `stg_yf__constituents` reads only the parquet ingestion
    writes. So a dbt-side correction cannot reach it, and does worse than nothing: `ingest.py:213`
    writes the ORIGINAL ticker into the fundamentals parquet and `dim_stock` joins on
    `(market_code, ticker)`, so an overridden ticker breaks that join, yields a null sector and
    currency, and fails eligibility outright. It also moves `base_yf__constituents`'s dedup
    partition key. Block stays off the deck exactly as it is now, silently. A ticker correction
    has to reach the
    fetch list, which is the first design question the new mechanism has to answer: whether the
    dbt model replaces the CSV as ingestion's input, or sits downstream of it.
    **Layer settled 2026-08-28.** The mapping is a dbt seed; a staging model exposes it as a
    direct source mapping; the override is applied in `2_base`, alongside the existing
    `base_yf__constituents`. Staging stays a source mapping and the business rule lives in base
    with the other entity resolution, which is the shape `docs/layering.md` describes. Stated
    precisely: that doc never mentions seeds, and `metric_catalogue.csv` is the only seed in the
    repo with no model referencing it, so the new contract ESTABLISHES this pattern rather than
    following one. Two things it will hit: `scripts/check_layer_contract.py:52` requires staging
    SQL under `1_staging/<source>/`, so the mapping model needs a subdirectory; and
    `_yfinance_staging.yml:32` still says the display name "may be overridden in core", which a
    base-applied override contradicts.
  - **ANSWERED 2026-08-28. Duplicate cards stay, and every card names its exchange.** The owner
    accepts one card per listing as the reality, and wants the listing venue shown on the card
    face so a reader meeting Shell twice can see why. That is the second of the two paths in the
    issue #7 escalation below, plus a card-face change. Not on this branch: it is user-facing
    layout and copy, so it goes through the UX PR gate on its own branch. Recorded here because
    it answers the escalation without closing all of it: naming the venue does not touch the two
    counters that say "companies" while counting card rows, which the issue #7 bullet records as
    remaining.
  - **Owner chose to batch by group rather than one market per branch, 2026-08-27.** The
    checklist ENDED "activate one market per audit cycle" when the decision was taken, a line
    this branch has since rewritten; each market here got its own coverage
    audit, which is what that rule protects, while the branch and review cycle are shared. The
    owner was given the literal-compliance option and the all-nine option and picked the middle.
  - **Owner chose OMXS 30 for Sweden, 2026-08-27.** Not in this batch, recorded because it was
    the open index decision the skill flagged. It matches the construction of the other Nordic
    indices already approved.
  - **Switzerland warns unless its coverage is perfect, and the threshold was NOT touched.** The
    SMI has 20 constituents and `scripts/check_pipeline_completeness.py:90` warns on a strict
    `eligible < WARN_ELIGIBLE_THRESHOLD` of 20, so 20 out of 20 clears it and anything less does
    not; the sample projects 19. Escalated rather than absorbed, because lowering a gate so the
    current work passes is the specific failure the France branch was pulled up for. The owner
    approved proceeding.
    **The basis given for that approval was wrong, and the owner has been told.** It said
    `--write-baseline` would set a per-market `min_eligible` floor after the first run, after
    which the warn would stop binding. Verified false: `scripts/check_eligibility_baseline.py`
    writes `min_eligible: 5` as a hardcoded literal on every rewrite and populates only
    `baseline_eligible`, and the 20 is a module constant in a different script that no baseline
    file can reach. The decision to proceed still holds on its own terms, since a WARN does not
    fail the job, but it was taken on a self-correction that does not exist.
    Of the four queued indices already chosen, only OBX is close, and not equally: at 25 members
    it needs 80 percent eligibility to clear a threshold of 20, where the SMI needs all 20 of
    its 20. OMXS 30 is 30, FTSE MIB is 40 and TSX 60 is 60; Finland's and Denmark's indices have
    not been picked. Whether to leave the gate or make it proportional to each market's
    constituent count is the owner's. ANSWERED 2026-08-28: the threshold is wrong and becomes
    proportional in phase 2. See the answered bullet at the top of this list.
  - **CHF display was the owner's and is now ANSWERED (2026-08-28): it stays as "CHF".** The rule
    is to use each currency's real-world form, and "CHF" is that form. The record of how the
    question arose follows, because the grounds for deferring it were wrong twice and that is
    worth keeping. Switzerland brings the first currency
    with no `_CURRENCY_SYMBOLS` entry, and money formats are user-visible under section 6. The
    grounds for deferring it were withdrawn: see the impact_map. It is also out of the standing
    currency proposal in `.claude/active_work.md`, not because it has shipped (nothing on this
    branch has) but because activating the market commits the treatment to the next run, which
    is what makes it a decision rather than a proposal.
  - **Issue #7 covers at least eleven companies, not one, and six of them predate this branch.**
    The deck shows one card per seed row, so a company in two indices is met twice. The owner was
    previously asked to weigh issue #7 against ArcelorMittal alone, which is not a decision
    anyone could take on the real facts.
    **Already duplicated before this branch (six):** Amcor, Newmont, ResMed (US and AU dual
    listings), Rio Tinto (UK and AU), News Corp (US and AU), and Airbus. "Before this branch" is
    seed-level, not deck-level: Airbus's second card also waits on the next run, since France has
    not run either, so five of the eleven are visible to a user today.
    **Added by this branch (five):** Shell, Unilever, RELX and IAG at two
    cards each, and ArcelorMittal going from ONE card to three, since only the CAC 40 row
    predates the branch. Eleven once the next pipeline run publishes them; nothing changes at
    merge, because no card exists for the new markets until that run.
    **A SECOND duplicate class exists that neither guard can see and neither path below fixes.**
    The eleven above are one company in two MARKETS. `us_sp500` separately carries three
    companies twice each in ONE market, as two share classes: Alphabet (`GOOGL` and `GOOG`), Fox
    (`FOXA` and `FOX`) and News Corp (`NWSA` and `NWS`). Both guards miss them, correctly: the
    names differ by the class suffix, and there is only one market. News Corp is in BOTH lists,
    so the distinct population is **thirteen companies**, not fourteen: the eleven above, plus
    Alphabet and Fox. Those thirteen carry 28 cards between them, 15 more than one each. News
    Corp alone is a three card company (two US classes plus the ASX line). Share classes are
    genuine separate index constituents and the class is named in the headline, so those cards do
    not mislead individually.
    **They are the only duplicates that move a PEER-SET number today.** Spain may add one on the
    next run: if Yahoo files both Acciona SA and Acciona Energia under Utilities, that peer set
    holds a parent and a subsidiary it consolidates, which pulls in the same DIRECTION without
    being the same mechanism: share classes duplicate one issuer's identical fundamentals, while
    these are two issuers whose economics overlap. Note the certain half is the peer COUNT, which
    the model selects ungated; Utilities sits at 7 without Acciona SA and 8 with it, so the flip
    is from no comparison at all to one drawn over 8 rows for 7 independent issuers.
    Legitimate index membership rather than a defect, and phase-2 threshold work, but it is why
    this sentence says today. Cross-market pairs land in
    different `(market_code, sector)` peer sets and cannot double count; these three all sit in
    `us_sp500` Communication Services, so that sector's `sector_peer_count` and its medians are
    computed over six rows representing three issuers. A repeated value cannot move a min or a
    max, so the count and the medians carry effectively all of the distortion; share classes
    price slightly apart, so de-duplicating could shift an extreme by that spread. Sector labels
    come from Yahoo rather than from
    the repo, so that grouping is expected rather than verified here. Pre-existing, outside this
    branch's scope, and it belongs with the phase-2 threshold work.
    `frontend/card_copy.py:152` renders "{sector} (N companies)" straight from
    `sector_peer_count`, so it is the reader-facing face of that same peer-set distortion: it
    overstates by up to 3 in one sector and cross-market duplicates cannot move it at all. A
    ceiling on the same grounds as the two below, since the benchmark CTE applies the same
    `is_card_eligible` filter.
    **Cross-market duplicates move a different number, and this is where the two paths actually
    differ.** `frontend/explore_filters.py:159` renders "N companies worldwide", and
    `frontend/markets.py:56` renders "N card-ready companies" (the no-hero fallback; the branch
    users actually hit renders the same inflated total without the word). Both count card rows,
    so BOTH duplicate classes inflate them. Today by 8 (5 cross-market, 3 share
    class); once the four unrun markets publish, by 15 (12 and 3). Those are ceilings: the two
    counters count card-eligible rows only, and whether every duplicate row clears eligibility
    is not checkable from here.
    **Thirteen is a floor, not a total.** `KNOWN_CROSS_MARKET_COMPANIES` keys on a
    punctuation-insensitive form, which is what lets it hold News Corp at all: `us_sp500` spells
    it "News Corp (Class B)" and `au_asx200` "News Corp Class B". Two classes remain invisible to
    it. A company whose two seeds differ by more than punctuation, an abbreviation or a suffix
    one source carries and the other does not, still slips through. And the same-market case is
    out of scope by construction, which is the share-class trio above. Block is a fourteenth
    candidate and a separate defect: see
    `notes`.
    Rio Tinto is the one arguable case, and sharper than "two legal entities": Rio Tinto plc and
    Rio Tinto Limited publish the same consolidated group accounts against two different market
    capitalisations, so two cards would show one set of financials with diverging valuation
    metrics, for a reader who is told they are the same company.
    **Two paths, no preference. Neither covers the same-market share-class case**, because both
    turn on distinguishing venues and Alphabet's two classes share one.
    ONE CARD PER COMPANY: pick a primary listing per company and suppress the rest. Needs a rule
    for choosing (largest market cap? index seniority?), and silently removes a company from a
    market a user has filtered to. Needs a second, separate rule for share classes, which have no
    venue to choose between. On its own it corrects 5 of today's 8 and 12 of the eventual 15 on
    the two listing counts, the share-class rule being what closes the rest and the sector peer
    count. **It also moves already-shipped numbers**, which the impact_map treats as this
    branch's safety criterion and section 6 reserves. Suppressing a listing removes that row
    from the eligible set in `int_stock__sector_benchmarks.sql`, so the peer count, medians AND
    the min and max recompute for **the market that LOSES the row**, not the one that keeps the
    primary listing: the grouping is `(market_code, sector)`, so the surviving market's own
    group is untouched. A sector sitting on exactly 8 drops to 7 and nulls every benchmark
    column, removing the comparison from every card in it. Both markets in all five live pairs
    have shipped, so whichever listing is chosen as primary, shipped numbers move.
    One qualification: this holds only if the suppression is applied at or above
    `is_card_eligible`. Suppressing in the mart instead would leave every row in the benchmark
    pool and move nothing, at the cost of the two counters staying wrong.
    ONE CARD PER LISTING WITH THE VENUE NAMED: keep both rows and label each with its venue.
    Costs a card-face change. Adds no Haiku spend against today, since the deck already pays for
    every row; costs one read per duplicate more than path 1 would. Leaves the share-class case
    as it is, the class already being in the headline. Leaves both listing counts saying
    "companies" while counting card rows, unless that copy changes too. Changes no
    already-shipped number, since every row stays in the benchmark pool.
  - **`MT.AS` (ArcelorMittal) is a real dual-index membership, not a copied seed.** The CAC 40
    and AEX pages list it independently and both give the Amsterdam line, so the seeds agree by
    fact. Added to `KNOWN_DUAL_INDEX_SYMBOLS` with the market pair and reason, per checklist step
    10, rather than editing either seed. **The deck will show ArcelorMittal three times, not
    twice**: `MT.AS` under `fr_cac40` and `nl_aex`, plus `MTS.MC`, its Madrid line, under
    `es_ibex35`. The collision guard is keyed on the resolved Yahoo symbol and so cannot see the
    third. That sentence is about the SYMBOL-keyed guard specifically; the company-name guard
    added on this branch does see `MTS.MC`. Issue #7 covers the display fix.
  - **SMI card headlines are in a different register from every other market, and two are wrong.**
    ESCALATED, and ANSWERED 2026-08-28 as to mechanism: corrections move into a dbt model rather
    than hand edits. Which names are right is still an owner review of the resulting list. The
    Swiss source table's only name column gives legal names, so the
    seed carries "Novartis International AG", "Swiss Reinsurance Company Ltd" and "Holcim
    Limited" where the other eight markets carry trade names. The listed issuers are Novartis AG
    and Swiss Re AG, and yfinance's `info_long_name` has them right, but `dim_stock.sql:23`
    prefers the seed name, so the coalesce discards the correct one. Verified there is no config
    fix: the SMI table's columns are Rank, Name, Sector, Ticker, Canton, Weighting, with no
    short-name column, so anything durable is a new override mechanism. Both the naming and the
    mechanism are section 6.
  - **The Discover market filter will offer four markets with no cards, from merge until the
    next run.** `frontend/explore_filters.py:16` builds its options from `MARKET_DISPLAY_NAMES`
    rather than from the deck, so CAC 40, AEX, SMI and IBEX 35 appear as soon as this merges.
    This is the same overclaim the About panel was rewritten to remove, on a more prominent
    surface, and fixing it here would be scope creep on an onboarding branch. Recorded for the
    owner rather than absorbed, and it resolves itself on the next pipeline run.
  - **`frontend/overflow_menu.py`'s markets line now derives from the cards in the deck.** It was
    the literal "Markets: US, UK, Japan, Australia, Germany". A first attempt derived it from
    `MARKET_DISPLAY_NAMES`, which was worse: a market is onboarded on one branch and first
    exports cards on the next production run, so that version claimed nine markets while the live
    deck holds five, and contradicted the per-market breakdown printed four lines below it in the
    same panel. Deriving from `counts` is right on both sides of a run and makes the two lines
    agree by construction. The copy change that remains for the owner is the register: it now
    reads index names ("S&P 500, FTSE 100, ...") rather than country names, because the registry
    holds no country label and inventing one is new data.

done_when:
  - All eleven checklist steps done for all three markets, in the order the checklist gives.
  - Each market has: `ingest_active: true`, a `constituent_sources.yml` entry, a generated seed,
    an entry in `dbt_project.yml` written by `sync_dbt_vars.py`, a `public.markets` row in
    migration 015, a display name, and an `_EXCHANGE_SUFFIX` entry.
  - Step 4 done per market, not assumed: all 80 tickers resolve AND return a populated sector
    and currency. No stub like France's `ML.PA` in this batch.
  - Step 5 sample audits recorded: 80% (NL), 95% (CH), 75% (ES) estimated card-eligible. The
    full-run half of step 5 and the confirmation half of step 6 are NOT satisfied and cannot be
    from here; they are recorded as open in `.claude/active_work.md`.
  - `company_name` reaches the card headline, so every active seed is free of scrape artifacts.
    Fixed at the writer, not in the CSV: `_clean_company_name` strips trailing LOWERCASE markers
    (`[es]`, `[1]`, `[a]`, `[note 1]`, and chains of them) and eleven invisible or exotic space
    characters, on every refresh path. Uppercase bracketed tokens are left alone deliberately:
    `[A]`, `[B]`, `[AB]`, `[ASA]`, `[NV]` are Nordic share classes and legal forms, four of the
    six queued markets are named on that convention, and `write_constituents` de-duplicates on
    ticker rather than name, so collapsing two names would ship two cards with one headline.
  - The seed guard in `test_market_onboarding.py` is WIDER than the cleaner in all THREE of its
    halves, so it fails on artifact classes the cleaner deliberately does not touch rather than
    confirming the cleaner's own regex. Measured in each case, because two earlier versions
    claimed coverage they did not have. Whitespace: the guard flags 23 code points the cleaner
    never strips, 22 of them whitespace to Python plus U+180E, which is a format character
    (tabs, newlines, U+1680, U+2000-U+2004, U+2008, U+200A, U+2028, U+2029, U+205F, U+3000 among
    them) and any trailing bracket up to 20 characters, uppercase included. Non-bracket footnote
    markers are the third half, added after a reviewer pointed out that widening the GUARD costs
    nothing since it only ever fails loudly. The class is the classic footnote sequence
    (`*`, dagger, double dagger, section, double vertical line, pilcrow), the reference mark,
    the asterism, the low asterisk, and the superscripts and subscripts of both Unicode blocks:
    60 code points below U+3200. Two versions of it were wrong before this one. The first missed
    superscript one, two and three, which live in Latin-1 rather than the superscript block and
    are the likeliest markers of all; the second held the asterism and the low asterisk with no
    case exercising either. Neither was detectable, because nothing exercised the regex at all.
    `test_seed_guard_catches_non_bracket_markers` now runs 21 cases, 16 expecting a fire and 5
    not; replacing the regex with one that never matches used to leave the suite green and now
    fails 16 tests.
  - `tests/ingestion/test_constituent_seeds.py` pins the cleaner in BOTH directions, proven by
    mutation against the staged tests: widening it to eat any trailing bracket fails 8, restoring
    the uppercase version fails 6, reverting to the round-2 regex fails 2, the unmutated control
    passes 34. Over-stripping silently rewrites a headline and no outcome-only guard can see it.
  - `test_seed_company_names_are_unique_within_a_market` pins the consequence rather than the
    mechanism: two rows whose headlines render the same, however they got that way. Matching is
    punctuation-insensitive, which is not cosmetic: the exact version of this guard shipped
    through round 10 and missed a live wrong-company card, because the two headlines differ only
    by full stops. It is still not a uniqueness proof, since two rows naming different
    companies with different strings look correct from here. It found two real defects that
    way, and a full audit then found nine more.
    **The worse one: `jp_nikkei225` ticker 9101 is Nippon Yusen (NYK Line) and carries the name
    "Mitsui O.S.K. Lines", which is ticker 9104 on the next line.** So a live card shows one
    shipping line's
    financials under a competitor's name, and Nippon Yusen is absent from the deck entirely.
    Attributing one company's accounts to another is the worst defect class this app can put in
    front of a beginner, and it is live in a market that has run.
    The other one the guard caught: ticker 3407 is Asahi Kasei and carries the name "Asahi Group
    Holdings", which is ticker 2502.
    **A full audit of the seed against yfinance on 2026-08-28 found ELEVEN wrong company names
    in 116 rows.** Besides 9101 and 3407: 6908 is Iriso Electronics named "Iris Ohyama", 6976 is
    Taiyo Yuden named "Canon Electronics", 8005 is Scroll Corporation named "Showa Shell
    Sekiyu", 8804 is Tokyo Tatemono named "City Development", 8830 is Sumitomo Realty named
    "SUMCO", 9005 is Tokyu named "Keio Corp", 9008 is Keio named "Keisei Electric Railway",
    9009 is Keisei named "Keihan Holdings", and 9412 is SKY Perfect JSAT named "Skylark
    Holdings". An earlier draft called the railway rows "shifted by exactly one row" and inferred
    a column misalignment in the import. The seed disproves that: rows run 9001 Tobu (correct),
    9005 "Keio Corp", 9007 Odakyu (CORRECT), 9008 "Keisei", 9009 "Keihan", so a correct row sits
    between two wrong ones and no column slide produces that. What the seed supports and no
    more: all three carry another railway's name, 9008 and 9009 are adjacent while 9005 is two
    rows off, and Keihan's real ticker 9045 is not in the seed at all. They share no single
    offset, and a draft claiming they carried "the next Tokyo private railway's name" was wrong
    twice over: Keikyu and Odakyu sit between 9005 and Keio's 9008, and Keihan is an
    Osaka-Kyoto operator. The other eight fit no shift either:
    Iris Ohyama is unlisted, Showa Shell delisted in 2019, and Skylark is ticker 3197. The cause
    is not established. `jp_nikkei225` is the only seed with `source: import`, and the starter
    file it came from has identical row order. **Only two of the eleven are visible
    to any guard in this repo**, because a wrong name whose true owner is not also a row in the
    same seed looks correct from here. Filed with the full table; the durable fix is comparing
    each seed name against `info_long_name`, which is a new mechanism and the owner's call.
    Whether both rows cleared eligibility in the last run is not
    checkable from here, so the live effect is either two cards sharing a headline or one card
    naming the wrong company. Either way a reader is told the wrong company. Pre-existing since
    the 2026-05-23 import and NOT caused by this branch; it is
    allowlisted with that reason, with a second test that fails if the allowlist outlives the
    defect. Fixing it edits a shipped card headline and belongs on its own branch.
  - UX gate (`docs/working_agreement.md`): one user-facing copy line changed, in the overflow
    menu's "About the data" panel. A second user-facing surface changes without a code edit: the
    Discover market filter enumerates `MARKET_DISPLAY_NAMES`, so AEX, SMI and IBEX 35 appear in
    it from merge, before any of their cards exist. See `decisions_reserved`. No layout, tab
    behaviour or interaction change, so points 1,
    2 and 4 do not apply. Point 3, one sentence on what the user can do after merge: a user
    opening "About the data" sees the markets the deck actually contains, instead of a list
    written by hand that has been wrong since France merged. Point 5: the line is plain wrapping
    markdown text, at most 79 characters at nine markets, and adds no fixed-width element, so it
    cannot introduce horizontal scroll at 480px. Reasoned, not measured on a device: the app
    needs Supabase credentials this branch does not have.
  - `scripts/eligibility_baseline.ci.json` reflects nine markets (63 = 9 x 7 fixtures).
  - `tests/ingestion/test_market_onboarding.py` green, including the collision guard, which
    fired on `MT.AS` before the allowlist entry was added and passes after it.
  - pytest green, `dbt build` green on `--full-refresh` after `seed_ci_raw_fixtures.py`, and the
    five CI gates that run without a warehouse or credentials green: `check_layer_contract`,
    `check_registry_var_sync`, `check_dbt_tests`, `check_dbt_documentation`,
    `check_dbt_sql_structure`. The other three `check_*` jobs in `.gitlab-ci.yml` need a built
    DuckDB; `check_eligibility_baseline` and `check_eligibility_gaps` were run against the local
    build and pass at 63, and `check_export_health` needs Supabase credentials and was not run.
  - No em dash or en dash introduced.

notes:
  - The Swiss source table gives BARE tickers (`NOVN`, not `NOVN.SW`), unlike the Dutch and
    Spanish tables. `frontend/live_quote.py`'s `_EXCHANGE_SUFFIX` is therefore load-bearing for
    Switzerland, where it is inert for France. The checklist warns about exactly this.
  - **`Laboratorios Rovi [es]` shipped from the IBEX 35 table with a Wikipedia interlanguage
    marker and a non-breaking space in front of it.** `dim_stock.sql:23` prefers the seed name
    over yfinance's `info_long_name`, so it would have been the card headline. CI never reads a
    real seed (the fixture seeder synthesises names), which is why nothing caught it.
  - **Nothing in the repo detects a constituent that fetches no data, and this branch adds 80
    more tickers to that blind spot.** `check_pipeline_completeness.py:30` counts seed rows and
    only ever tests for zero; nothing compares seed rows against fundamentals rows per market.
    That is why the Block ticker survived since May, and fixing one keystroke by hand leaves the
    next typo equally invisible. The detector belongs in the same contract as the name mapping,
    since a seed-versus-fundamentals join is where it becomes checkable. Pre-existing, not
    introduced here, and not built here.
  - **`au_asx200` has been silently ingesting nothing for Block since May, and this branch found
    it but did not fix it.** The seed says ticker `XYX`; `XYX.AX` and `SQ2.AX` both 404 on Yahoo
    while `XYZ.AX` resolves to Block, Inc. in AUD. One keystroke. Nothing detects a constituent
    that fetches no data, which is why it survived. Out of scope here (the seed is another
    market's and fixing it adds a card to a shipped deck, which is section 6), filed separately
    alongside the Nikkei naming defect.
  - The Swiss seed carries the bare ticker `ROP`, which resolves to `ROP.SW`. That is correct and
    is Roche Holding AG, CHF, Healthcare, 290bn market cap; `ROG.SW`, the more familiar symbol,
    404s on Yahoo, and the SMI source table itself gives ROP. Recorded because the pair looks
    like a typo and a later reader would otherwise re-derive it. One reviewer noted ROP is
    Roche's bearer line rather than the non-voting Genussschein and could not check it offline;
    the fetched source table and the live symbol lookup both agree with the seed.
  - The Swiss Wikipedia table has 21 rows, the last of them entirely empty; the seed writer drops
    it and the seed holds the correct 20 constituents. The refresh script's "21 tickers" line
    counts raw table rows, not written ones.
