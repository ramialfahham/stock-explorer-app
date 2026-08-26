# Task contract

objective: Stop the app naming a currency that is not the company's, and stop the prose
  blaming the health verdict on positive revenue growth. The 2026-08-26 pipeline run made
  both visible for the first time: 246 of 921 generated reads (27%) used a currency word
  belonging to another market, and 83 described positive-but-slow growth as the weakness
  holding the badge back. Prompt and card copy only. No verdict rule change, no threshold
  change, no new metric. Sector-calibrated thresholds are step 3 and are NOT in this branch.

scope_paths:
  - scripts/assessment_rules.py
  - scripts/generate_assessments.py
  - docs/data_contract.md
  - dbt_analytics/seeds/metric_catalogue.csv
  - frontend/card_copy.py
  - frontend/metrics.json
  - docs/ux_principles_finanz_lern_apps.md
  - tests/tooling/test_assessment_rules.py
  - tests/frontend/test_card_copy.py
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/active_work.md

impact_map:
  - Every one of the ~921 live cards regenerates its prose read on the next pipeline run
    (`INPUT_HASH_VERSION` 5a.3 -> 5a.4), so ~921 Haiku calls and a full rewrite of the
    user-facing paragraph on every card in every market.
  - The card FACE changes immediately on merge, with no pipeline run needed: `gloss`,
    `analogy`, `learn` and `label` are bound by `frontend/card_copy.py` and read from
    `frontend/metrics.json`, which is generated from the seed. Affects every card in all five
    markets, not only the non-US ones, because these strings are shared. `interpretation` is
    also edited and also exported, but no frontend module binds it today, so that column
    ships to the client unrendered.
  - `mart_stock_cards` and every dbt model are untouched. `dbt build` is 108/108 on a
    `--full-refresh` seed reload.
  - No Supabase migration: no column added or renamed.

decisions_reserved:
  - **All replacement strings are §6 owner-signed content and need sign-off before commit.**
    `READ_SYSTEM_PROMPT`, `READ_METRIC_BRIEF` and the `metric_catalogue.csv` copy are what
    the reader sees. The owner approved fixing the two defects and approved widening the
    branch to the card copy; the exact wording is proposed here, not decided by the agent.
  - **`INPUT_HASH_VERSION` 5a.3 -> 5a.4: OWNER-APPROVED.** API volume is a §6 cost decision
    and was escalated rather than assumed. The owner approved the bump, on the ground that
    without it the corrected prompt ships and every stored read keeps its current defective
    prose: the hash covers the metric inputs, the verdict and the version, never the prompt
    text, so nothing would mark the old prose stale. Cost is ~921 Haiku calls on the next run,
    the same volume as the 2026-08-26 run. Note the card-face copy in this branch needs no
    run at all; it is the AI paragraph alone that depends on this bump.
  - **The per-unit idiom is KEPT, not banned.** An earlier draft of this branch forbade
    explaining a margin as an amount per unit sold. The owner rejected that: "actually, this
    is easy to understand for beginners." Correct, and it reframed the defect. The idiom is
    good teaching; naming the WRONG currency is the bug. So the rule now permits the idiom
    and anchors it to a stated currency. Do not re-ban it.
  - **The prompt names the DISPLAY currency, and says so.** The mart's `currency` is
    `coalesce(info_currency, dim_stock.currency)`, documented as a display code. The true
    reporting currency is `stmt_currency`, which exists in `fct_fundamentals_snapshot` and is
    NOT carried into the mart, so this branch cannot state it. Two labels were tried and both
    were false: "Reports in" asserts an accounting fact the pipeline does not have, and
    "Currency shown on this card" is false on operating and financial cards, which render no
    money at all (only the three `currency_compact` metrics do, all `pre_revenue`). The line
    now reads "Currency this company trades in", which is what `info_currency` actually is.
    **Known limitation, not fixed here:** a
    company that files in one currency and trades in another gets a read denominated in the
    trading currency. Correcting that needs `stmt_currency` plumbed to the mart, an export
    column and a migration. Owner's call whether that is worth doing.
  - **`GBp` is pence, and is normalised to GBP.** yfinance reports LSE tickers in pence; 89
    of 92 FTSE cards carry `GBp`. Every other consumer upper-cases before formatting, so the
    card face already shows a pound sign. Passing the raw code would name the model a unit
    that appears nowhere on the card.
  - **Growth: the prose must not supply a reason the badge does not contain, and must not
    deny that a flat top line is a weakness.** The verdict downgrades only on an actual
    year-over-year decline (`GROWTH_DECLINE_THRESHOLD_PCT = 0.0`), so blaming the badge on
    positive growth invents a reason and re-establishes the two-sided axis the design
    forbids. An earlier draft over-corrected to "growth that is positive is never a weakness,
    however small", which is false: +0.2% is a real-terms decline in every market this app
    covers, and teaching a beginner otherwise is the mirror image of the defect. The rule now
    bars only the verdict attribution and explicitly allows describing a flat top line
    accurately. Do NOT fix this by making growth a two-sided axis in the rules.
  - **`currency` is now hashed, which the module docstring's invariant did not allow for.**
    It is a prompt input the read quotes, so a corrected currency must regenerate the read.
    Hashed through `_display_currency` so a GBp/GBP case change, invisible on the card, does
    not churn ~90 FTSE reads for nothing. Docstring updated to name the exception rather than
    left asserting something false.
  - **Em dashes left in place, owner's call.** `frontend/card_copy.py` and
    `docs/ux_principles_finanz_lern_apps.md` are touched by this branch and carry 13 and 15
    pre-existing em dashes respectively. Two of them, `card_copy.py:261` and `:341`, are the
    user-visible "no value" placeholder glyph on the card face, so changing them alters
    rendered UI and is §6 product content, not a cleanup. The rest are code comments. This
    branch introduces none. It sweeps `assessment_rules.py`, whose prompt text it
    substantially rewrote, and removes one each from `docs/data_contract.md` and
    `.claude/active_work.md` as a side effect of rewriting those passages. It does NOT sweep
    the two files above. Doing so is a separate decision.
  - **`revenue_growth_yoy_pct`'s `learn` copy is left alone, deliberately.** MR !43 recorded
    it as an OPEN owner question: it says "One quarter can be noisy, so look for a pattern
    over time" and renders on cards the growth gate downgrades, so a reader sees a badge that
    moved on one quarter beside text saying one quarter is noisy. This branch now owns that
    file, but the question is about the VERDICT's use of growth, not about currency, and
    answering it here would decide an escalation that belongs to its own thread. Still open;
    also recorded in `.claude/active_work.md`.
  - Not in scope, flagged not fixed: 25 of the 921 reads use an ASCII hyphen as sentence
    punctuation. The existing rule forbids em and en dashes by name and permits hyphens in
    compounds, so this is within the letter of the rule. Whether to tighten it is the owner's
    call.
  - Not in scope: the card shows sector-relative benchmark words (`card_copy.py` compares to
    `sector_median_*`) while the verdict uses global absolute bars, so a Utilities card can
    read "lower than most in its sector" under a red badge. Pre-existing and belongs to step 3.
  - **Three places state the input-hash payload and all three had to move together.** The
    module docstring, `docs/data_contract.md` and `scripts/generate_assessments.py`'s column
    comment (which asserted `currency` "is NOT hashed/scored"). Fixing one and leaving the
    others would ship a false invariant in the authoritative doc, so both files were added to
    `scope_paths` rather than flagged and left.

done_when:
  - No `READ_METRIC_BRIEF` gloss for a non-money metric names a currency word or symbol.
  - `metric_catalogue.csv` carries no currency word or symbol in any user-visible field
    (`interpretation`, `gloss`, `analogy`, `learn`, `label`, `applicability`), enforced by
    `test_catalogue_user_visible_copy_names_no_currency` rather than by grep. The repo-wide
    sweep for "sales dollar" / "each dollar" / "revenue dollar" is clean apart from four
    deliberate sites: this contract, `.claude/active_work.md` and
    `tests/tooling/test_assessment_rules.py`, which quote the defect in order to describe or
    detect it, and `docs/handover_2026-08-18.md`, which is archived history.
  - `frontend/metrics.json` regenerated from the seed by
    `scripts/export_metric_definitions_json.py`, so the card face matches the catalogue.
  - `build_read_messages` names the card's currency for EVERY company type, normalised
    through `_display_currency`, and omits the line entirely when it is absent.
  - `READ_SYSTEM_PROMPT` scopes the per-unit idiom to margins, states that returns and growth
    have different denominators, and tells the model what to do when no currency is given.
  - `READ_SYSTEM_PROMPT` bars blaming the verdict on positive growth while still allowing an
    accurate description of a flat top line.
  - The growth gloss still contains "counts against the verdict" and "does not count for it",
    pinned against the BUILT message.
  - `currency` is in the hashed payload; `INPUT_HASH_VERSION` bumped.
  - No NEW em dash or en dash is introduced by this diff. A full sweep of the two touched
    files that still carry pre-existing ones is NOT claimed: see decisions_reserved.
  - 17 new test functions (32 -> 49); 15 of the 51 collected items fail against the pre-fix
    `scripts/assessment_rules.py` and `metric_catalogue.csv`. The rest are regression guards
    that pass both ways, by design. Measure these, never estimate them: this clause was wrong
    twice, in both directions, because it was written from memory between edits.
  - Every EDITABLE statement of the input-hash payload agrees with the code: the module
    docstring, `docs/data_contract.md` and `scripts/generate_assessments.py`'s column comment.
    `supabase/migrations/010_card_assessments.sql` states it too and is deliberately NOT
    updated: it is already applied, the runner tracks by filename with no checksum, so an edit
    could never reach the database and would only make the repo describe a comment that
    differs from the live one. Applied migrations are immutable.
  - The UX PR gate in `docs/working_agreement.md` is satisfied for the card-copy change: the
    app was run and read at 375px (stricter than the gate's 480px), no horizontal overflow,
    and every reworded string was verified through `frontend/card_copy.py`'s real render path
    rather than trusting the seed. No layout, interaction or tab behaviour changed, so items 1,
    2 and 4 do not apply; item 3's one-sentence job statement goes in the MR description.
  - No catalogue copy for a `financial`-only metric uses the word "sale".
  - `frontend/card_copy.py`'s hardcoded analogy overrides are guarded too. They bypass the
    catalogue entirely, so the seed guard cannot see them: that is a second home for the same
    defect and it needs its own check (`tests/frontend/test_card_copy.py`, which fails against
    the pre-fix `card_copy.py`).
  - pytest green, `dbt build` green on a `--full-refresh` seed reload, the five CI gate
    scripts green, and the owner has signed off on the exact strings.
