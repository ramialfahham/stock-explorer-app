# Task contract

objective: Stop showing metrics that depend on the share price, so that every metric on a
  card can feed the verdict. Drop `forward_pe`, `price_to_tangible_book` and
  `dividend_yield_pct` from the catalogue, and replace pre-revenue's
  `net_cash_to_market_cap` (a ratio against market cap) with `net_cash`, the same idea as a
  money amount. Step 1 of three; the verdict redesign and sector-calibrated thresholds are
  separate branches.

scope_paths:
  - dbt_analytics/seeds/metric_catalogue.csv
  - dbt_analytics/models/4_intermediate/int_stock__card_metrics.sql
  - dbt_analytics/models/4_intermediate/_intermediate.yml
  - dbt_analytics/models/5_marts/mart_stock_cards.sql
  - dbt_analytics/models/5_marts/_marts.yml
  - supabase/migrations/013_net_cash.sql
  - scripts/export_to_supabase.py
  - scripts/assessment_rules.py
  - scripts/seed_ci_raw_fixtures.py
  - dbt_analytics/tests/assert_eligible_mart_rows_have_all_metrics.sql
  - frontend/metric_school.py
  - frontend/card_copy.py
  - docs/ux_principles_finanz_lern_apps.md
  - docs/ui/card_metric_cell.md
  - docs/engineering_standards.md
  - dbt_analytics/models/_docs.md
  - frontend/metrics.json
  - docs/data_contract.md
  - tests/**
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/active_work.md

decisions_reserved:
  - **Why these three metrics go, owner-decided 2026-08-26.** Two reasons, both the owner's.
    First: "If we don't use a metric for the verdict then we don't show it" — the card showed
    8 metrics while the verdict used 6, and led with Forward P/E, which the verdict ignores
    entirely. Second, on Forward P/E specifically: "as we have the stock price in it and we
    update every twice a month, it is questionable to show it at all". The agent's separate
    objection — that price-based metrics would make a health verdict move with the share
    price, which is a buy signal — is ALSO resolved by removing them, but it was not the
    owner's reason and must not be recorded as such.
  - **The replacement is a money amount**, owner-chosen from two options put to them
    ("net cash as a money amount" vs "cash / total debt"). Same numerator as the metric it
    replaces, no denominator, so no share price and no divide-by-zero.
  - **NOT decided, and a real consequence to check:** a money amount has no scale-free
    "good" threshold, so the pre-revenue verdict's net-cash axis degrades from "net cash is
    at least 20% of market value" to "net cash is positive". Green becomes slightly easier
    to reach for pre-revenue cards. Flagged in the MR; not silently absorbed.
  - **NOT decided:** the exact user-visible copy for `net_cash` (label, gloss, analogy,
    learn). Adapted from the approved `net_cash_to_market_cap` copy by removing the price
    comparison, so the concept is the owner's and only the phrasing is derived. Listed in
    the MR for approval.
  - **`READ_SYSTEM_PROMPT` was reworded, and that is a §6 change.** `scripts/assessment_rules.py`
    marks that block "Owner-signed voice (§6)" twice, and the previous branch's contract said in
    terms: do not reword either rule without going back to the owner. Two edits were forced here,
    both factual rather than stylistic. The rule "Valuation (P/E, price-to-tangible-book) and
    growth are context only" now names growth alone and states that no valuation figure is passed
    to the model at all, because none exists; and `READ_METRIC_BRIEF`'s `net_cash` gloss was
    rewritten with the metric. Leaving the old wording would have instructed the model about
    metrics it can no longer be given. **Listed for the owner's approval alongside the `net_cash`
    copy, not treated as pre-approved.**
  - **Still open, raised by equity-analyst-reviewer and NOT closed here:** the bank card is now
    four profitability/returns/growth numbers, and nothing in any catalogue text tells a reader
    those numbers cannot judge a bank's capital adequacy or asset quality. `price_to_tangible_book`
    carried the only hint ("below 1 can signal doubts about asset quality") and it is gone. The
    limit survives only as an instruction in the LLM prompt, which CI pins for presence in the
    prompt but never in the generated read — so on a card with a null `ai_read` the warning
    reaches nobody. Closing it needs new bank-card copy, which is owner content.
  - Scope choice: stop SHOWING the three metrics (remove from the catalogue), do not rip
    their columns out of the warehouse. Ripping them out touches ~30 files across every dbt
    layer plus a Supabase migration, buys nothing today, and is hard to reverse.

done_when:
  - The three price-based metrics no longer appear on any card; `frontend/metrics.json` is
    regenerated from the seed and matches it (the no-drift lock).
  - `net_cash` is computed in the intermediate model, carried through the mart, exported to
    Supabase (with a migration adding the column), and renders as a money amount.
  - Eligibility no longer requires a metric the card does not show: `forward_pe` is dropped
    from the operating and financial eligibility tests, and pre-revenue keys on `net_cash`.
  - `scripts/assessment_rules.py` reads `net_cash` instead of `net_cash_to_market_cap`
    wherever the pre-revenue verdict and the prose brief reference it.
  - `dbt build` passes; pytest passes; the layer-contract and doc-check gates pass.
  - A dbt unit test pins the CHANGE's headline effect, not just its absence of breakage: an
    operating and a financial company with a null `forward_pe`, and a pre-revenue company
    with no market cap at all, must all now be eligible. Without this the eligibility change
    passes a green build with no row exercising the difference, which is exactly what
    happened on the first attempt.
  - UX gate (`docs/working_agreement.md`): this changes card composition — the bank card
    goes from 7 metrics to 4, the operating card's first lens changes from Valuation to
    Profitability (its only valuation metric is gone), the pre-revenue card reorders because
    net_cash moved lens, and a tab is removed from "Understand these numbers". Item 2
    (component specs) therefore applies and `docs/ui/card_metric_cell.md` is updated in this
    branch. Item 4's wireframe and item 5's 480px check go in the MR body.
  - Review cycle: scope-auditor, analytics-engineer-reviewer, cto-reviewer,
    data-engineer-reviewer (supabase/*) and equity-analyst-reviewer PASS.

impact_map: This changes what the deck contains, not just what a card shows.
  - **More cards will become eligible.** Operating and financial eligibility currently
    require `forward_pe` to be non-null; dropping that requirement admits companies Yahoo
    has no forward P/E for. The size of that increase CANNOT be measured before a run — the
    mart stores only eligible rows — so it will first appear in the next pipeline run's
    card count. Expect the count to rise above 907 and do not treat that as a regression.
  - **Bank cards lose 3 of their 7 metrics** (Forward P/E, price/tangible book, dividend
    yield), leaving growth, ROE, net margin and ROA. Three of those four are what the bank
    verdict reads; `revenue_growth_yoy_pct` is NOT — the verdict excludes growth on purpose.
    So the owner's rule ("if we don't use a metric for the verdict then we don't show it")
    is satisfied for valuation and still unsatisfied for growth, on both the bank and the
    operating card. That is step 2's job, not this branch's, and must not be described as
    already done.
  - Pre-revenue cards keep all four metrics; one changes shape from a ratio to an amount.
  - `sector_median_forward_pe` / min / max become dead columns in the mart and Supabase.
    Left in place deliberately (see scope choice); flagged for a later cleanup.
  - **Every stored AI read regenerates on the next pipeline run, ~910 Haiku calls.** Not from
    an `INPUT_HASH_VERSION` bump (still `5a.2`) but as a side effect: `compute_input_hash`
    hashes the per-type field set itself, and this change alters that set for ALL THREE
    company types, so every card's digest moves. That is arguably desirable — stored reads
    still discuss a P/E the card no longer shows — but API volume is an owner-level concern
    under §6 and it must be recorded rather than discovered. Found by cto-reviewer, not
    disclosed in the first draft of this contract.

amendments:
  - 2026-08-26 — round 1, three reviewers FAIL. The serious one: dropping `forward_pe` from
    the catalogue would have crashed the live app. `frontend/metric_school.py` rendered a
    "P/E" playground as tab 0 of the "Understand these numbers" panel, reading
    `METRIC_LABELS['forward_pe']` from the generated metrics.json — a `KeyError` on every
    card that opened the panel, with pytest staying green because the tests only import the
    seed helpers. The playground is removed. Also fixed: the `expression_is_true` eligibility
    mirrors in BOTH `_intermediate.yml` and `_marts.yml` still asserted the old rule and
    would have gone red on the first company the change admits; `net_cash` had no column
    documentation in either layer, which fails the doc gate; the Supabase migration created
    the column as `double precision` while every sibling metric column and this branch's own
    data contract say `numeric`; and stale prose in the export-contract dbt test, the CI raw
    fixtures, and four places in `docs/data_contract.md`. scope_paths widened for the three
    files that needed edits outside it. The analytics reviewer also established that the
    local build passed VACUOUSLY — no fixture row had a null forward_pe — which is why the
    new unit test above exists.
  - 2026-08-26 — round 2, three reviewers FAIL. `scope_paths` widened again, for
    `frontend/card_copy.py`, `docs/ui/card_metric_cell.md`, `docs/engineering_standards.md`
    and `dbt_analytics/models/_docs.md` — all four carried prose this change falsified, and
    `_docs.md` is the block `_intermediate.yml` points readers at for the eligibility rules.
    Also fixed: `test_hash_handles_nan_like_none` had been made VACUOUS by the diff (it
    mutated `forward_pe`, which left the hashed field set, so it asserted h == h and the NaN
    guard lost its only coverage); the metric_school crash was spot-fixed without closing the
    bug class, so a guard test now scans that file for label lookups and checks each id
    against the catalogue; and the full-deck Haiku regeneration was added to impact_map after
    cto-reviewer found it undisclosed.
  - 2026-08-26 — round 3, three reviewers FAIL. equity-analyst-reviewer found the `net_cash`
    copy I drafted was financially wrong in three ways, all now corrected: the analogy said
    net cash is "what is actually yours", which describes equity, not net cash, and breaks
    outright on the negative half of a range the metric's own text calls normal; the `learn`
    and `interpretation` text asserted a company "could repay every borrowing today", when
    `stmt_total_debt` excludes payables and other obligations AND `stmt_cash_and_equivalents`
    is the narrow row excluding short-term investments — where young companies actually hold
    their money, so the claim can be flatly false for exactly this metric's population; and
    nothing warned that a money amount is not scale-free, which is the very reason the
    verdict threshold had to collapse to zero. The same false wording sat in the LLM brief,
    instructing the model to write it onto live cards. Copy rewritten with both limits
    stated. **Still owner-pending as wording.**
  - 2026-08-26 — rounds 4 and 5, scope-auditor FAIL both times, on the same thing: stale
    prose surfacing one site per round. Round 4 also caught a fix applied to the WRONG row —
    a generic anchor matched twice and the "no longer catalogued" note landed on `roa_pct`,
    which is still catalogued and still on the bank card, while `price_to_tangible_book`
    (the row it was meant for) kept its "Rendered for financials" line. Reverted and
    reapplied correctly. Round 5 closed the lens counts, the module docstring and the
    worked example; round 6 closed the last two, one of which needed `scope_paths` widened
    again for `docs/ux_principles_finanz_lern_apps.md` (the playground spec, which described
    five playgrounds after this branch removed one). The lesson for the next branch that
    renames or drops a catalogued metric: sweep for the id AND for every count that
    describes the catalogue ("five metrics", "all 16", "the 5 with a range mark") in one
    pass, up front.
  - 2026-08-26 — round 7, scope-auditor FAIL: four MORE sites of the same class, all
    `sector_min_forward_pe` / `sector_max_forward_pe` still described as a "(card range
    mark)" in `_intermediate.yml` and `_marts.yml`, when no card can draw one now. Annotated
    as kept-but-unused. Round 8 then failed on THIS log for claiming the tail closed at
    round 6 — which is itself the lesson, so it is recorded rather than quietly corrected:
    **seven review rounds went on stale prose alone, always one or two sites at a time,
    because each sweep searched for the metric ids and not for the things said ABOUT them**
    (counts, lens lists, "card range mark", worked examples, playground inventories). A
    future branch dropping or renaming a catalogued metric should grep for the id, every
    catalogue count, and every phrase describing what the metric does, in one pass, before
    the first review round.
