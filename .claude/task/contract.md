# Task contract

objective: Separate the AI health assessment from the Yahoo company description on the
  card face — each in its own labelled block — so a reader can tell where each piece of
  text comes from.

scope_paths:
  - frontend/card_ui.py
  - frontend/card_copy.py
  - frontend/styles.py
  - scripts/assessment_rules.py
  - docs/ui/card_metric_cell.md
  - tests/frontend/test_card_ui.py
  - tests/frontend/test_styles.py
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/active_work.md

decisions_reserved:
  - Both label strings are user-visible copy (§6) and were chosen by the owner in-session
    on 2026-08-26, from options put to them. Verbatim: "What the numbers say · AI-written"
    for the assessment block, and "About the company" for the description block. The owner
    explicitly declined a source suffix on the second ("Option 2 without '· from Yahoo
    Finance'. I think we are communicationg the source somewhere else already") — confirmed
    correct: the About-the-data panel already reads "Sourced from Yahoo Finance via our
    pipeline, refreshed every two weeks."
  - The wording of the AI label was chosen over "AI summary" deliberately: the read is
    written from the card's figures, not condensed from a longer text, so "summary" would
    misdescribe it. Do not silently revert this to "summary" phrasing.
  - NOT decided here: whether the assessment panel should carry any further disclaimer
    beyond the label. Not raised, not assumed.
  - Verdict badge wording, owner-chosen 2026-08-26: Sturdy/Mixed/Strained becomes
    **Healthy/Mixed/Fragile**. The owner's objection to "sturdy" was that nobody uses the
    word. Strong/Weak was considered and rejected in the same exchange: it reads closer to
    a verdict on the SHARE than on the company's finances, and this app never implies buy
    or sell. Health framing also matches the section the badge sits in.
  - The two new READ_SYSTEM_PROMPT rules (no dashes as punctuation; do not write like a
    model) are owner-approved wording, drafted and signed off 2026-08-26 in response to em
    dashes appearing in live card text. The prompt is §6 content: do not reword either rule
    without going back to the owner.
  - NOT decided here, explicitly deferred by the owner: making the verdict BANDS
    sector-relative instead of fixed global thresholds. Raised in the same session after
    the owner asked where the rules came from and whether professionals use them. Honest
    answer given: the metrics are standard and the thresholds are conventional rules of
    thumb, but they are sector-blind, single-snapshot, and thin for banks (no CET1 from
    yfinance). Owner chose to ship labels + prompt rules first and design the band rework
    as its own slice. Do NOT quietly fold band changes into this branch.

done_when:
  - The card face renders two visually distinct blocks. The assessment panel (tinted,
    padded) contains the verdict badge FIRST, then the label "What the numbers say ·
    AI-written", then the prose. The label heads the prose only and is omitted entirely
    when `ai_read` is null — the verdict is rule-computed, so a heading claiming AI
    authorship must not sit above it. The company description sits outside that panel,
    label-first, under "About the company". The two blocks are therefore asymmetric
    (badge-then-label vs label-then-text) and that is deliberate, not an oversight.
  - Both headings use the existing small-uppercase accent treatment already used for the
    metric lens headings — no new visual language.
  - Every new CSS selector actually matches rendered DOM (this repo has shipped dead
    sibling-combinator and bare-class selectors six times across three MRs; the guard in
    tests/frontend/test_styles.py exists for exactly that).
  - The badge label and the model-facing VERDICT_MEANING stay in step, enforced by a test:
    the prompt tells the model to end its paragraph on the verdict's wording, so a drift
    between them would make a card's prose contradict its own badge.
  - INPUT_HASH_VERSION bumped, so every existing read is OFFERED for regeneration on the
    next pipeline run. Without it the change is invisible on live cards: reads regenerate on
    input-hash change and none of the NUMBERS moved, so the old em-dash "sturdy" text would
    survive. "Offered", not "guaranteed" — a card whose Haiku call fails keeps the new hash
    without new prose and may then be skipped. See impact_map below and the follow-up in
    `.claude/active_work.md`.
  - The metric gloss is visibly larger and lighter than the range mark's own min/median/max
    labels, verified by computed style on a live card, not by reading the CSS: gloss
    12.48px / rgb(161,161,170) against labels 11.52px / rgb(148,148,158).
  - `metric_gloss()` still ends on "Higher is better."/"Lower is better." — the cue was
    removed mid-task and restored; the function body must be byte-identical to HEAD with
    only its docstring changed, so the pre-existing cue tests pass untouched.
  - pytest passes; new tests cover both labels rendering and the panel wrapper.
  - Review cycle: scope-auditor + cto-reviewer (routed by scripts/*, frontend/*, tests/*)
    PASS against the staged diff. equity-analyst-reviewer added voluntarily, beyond what
    the routing requires: this changes financial wording on a live product surface.
  - `.claude/active_work.md` updated in the same commit — this changes a live, user-visible
    surface and the handover must not silently fall behind it.
  - UX gate (`docs/working_agreement.md`), item by item rather than in summary:
      - item 3 (one primary job): stated in the MR description.
      - item 4 (mobile wireframe for card structure changes): ASCII wireframe in the MR body.
      - item 5 (480px smoke): measured live, not eyeballed. At 480x900 every required
        element clears the fold. **At 480x740 the first metric value sits ~38px below it**
        — this change adds roughly 47px above the metric stack (two label lines plus the
        panel's border and padding), and the spacing was already trimmed to the minimum
        that still reads as a panel. The gate does not name a viewport height, so this is
        an owner call, surfaced rather than resolved by picking the height that passes.
      - item 1 (north_star): no tab behaviour change.
      - item 2 (component specs): the metric cell IS touched — the gloss is item 4 of
        `docs/ui/card_metric_cell.md`. Checked against that spec rather than waved past:
        the `0.5rem` top margin it pins (raised from `0.1rem` after earlier owner feedback)
        is unchanged, and the scoped `.ss-metric .ss-metric-gloss` selector it requires is
        preserved. The spec did not pin font-size or colour; it now records both, so the
        next change to either has something to check against.
  - NOTE: screenshots are not possible in this session — the browser pane is not displayed,
    so the page never composites frames and `computer{action:"screenshot"}` times out.
    Flagged before starting. Structure, computed styles and fold positions were verified
    live against a local Streamlit instance instead; visual sign-off is the owner's eye.

impact_map: Two surfaces, and they reach users differently.
  - **Frontend (immediate at merge):** the two labelled blocks and the new badge wording
    ship with Render's auto-deploy. `_health_block_html` and `_company_summary_html` are
    the only producers of this markup; the card face is their only caller.
  - **Generated prose (next pipeline run):** the prompt rules and the hash bump change
    nothing already stored in `card_assessments`. The bump advances the stored hash for
    every record, so every card is offered for regeneration on the next run — that run
    refreshed 907 rows on 2026-08-25, so expect roughly that many Haiku calls. "Offered",
    not "guaranteed": a card whose Haiku call fails keeps the new hash without new prose,
    and may then be skipped by the next run's regenerate test. See the note above
    INPUT_HASH_VERSION in `scripts/assessment_rules.py`; it is recorded as a follow-up in
    `.claude/active_work.md`, not fixed here (retrying stranded reads would be a new
    mechanism, and that is an owner call). (907 is the row count in a snapshot; the DECK is 910, see the card-count
    note in `.claude/active_work.md`. The two numbers are not interchangeable.)
  - **The mismatch window does NOT close for every card.** Between merge and the next run,
    cards show the NEW badge wording above OLD prose ending on "sturdy"/"strained", possibly
    with em dashes. For most cards that ends at the next run. It does NOT end for a ticker
    the pipeline stops exporting: `card_assessments` is unique per (market_code, ticker)
    (`supabase/migrations/010_card_assessments.sql`) and the frontend keeps the newest row
    per ticker, not the newest snapshot, so a dropped ticker keeps BOTH its stale card and
    its stale assessment indefinitely. Three such tickers exist today — BXB, RMS, SPK — and
    they will carry a "Healthy"/"Fragile" badge over "sturdy"/"strained" prose until they
    either come back or are evicted. Evicting them is the open owner decision already
    recorded in `.claude/active_work.md`; this branch does not resolve it.
  - No dbt model, no seed, no Supabase schema change.

amendments:
  - 2026-08-26 — scope widened by the owner mid-task, twice, both in-session. First: after
    seeing em dashes in live card text, the owner asked for the generation prompt and
    approved two new rules for it (`scripts/assessment_rules.py`). Second: the owner
    rejected the "Sturdy" badge label, and Healthy/Mixed/Fragile was chosen from options
    put to them (`frontend/card_copy.py`, plus the matching model-facing wording). Both
    paths added to scope_paths. The INPUT_HASH_VERSION bump came with them — it is not a
    separate decision but the mechanism that makes the prompt change reach existing cards.
  - 2026-08-26 — round 1, all three reviewers FAIL. Fixed here: a stale comment above
    READ_SYSTEM_PROMPT still describing the retired sturdy/strain wording; a hand-rolled
    `sys.path` insert in the test file duplicating `tests/conftest.py` and loading
    `assessment_rules` twice under two names; no test tying the new labels to the
    `.ss-card-identity` ancestry their CSS depends on; and two contract claims that were
    simply untrue (the mismatch window closing for every card, and 907 quoted as the deck
    size). equity-analyst-reviewer also found the AI label sitting ABOVE the rules-computed
    verdict badge, crediting the deterministic half of the assessment to the model — the
    badge now renders first and the label heads the prose only, and is omitted entirely
    when `ai_read` is null. The same reviewer found the new style rule could be read as
    licence to trim the required financial-company caveat; the rule now says in terms that
    it is style-only and never overrides a required limit. Two of that reviewer's findings
    are owner questions and are NOT resolved here: whether "Fragile" overstates a red that
    can fire on one weak axis of a single snapshot, and the 480px fold trade-off above.
  - 2026-08-26 — **AGENT-INITIATED, owner has NOT ruled on it.** Putting the badge above
    the label changes user-visible composition/ordering, which §6 reserves to the owner.
    It was made on a reviewer finding, not owner instruction, because the alternative was
    shipping a card that credits a deterministic rules engine to a language model. Raised
    with the owner in the session report and called out in the MR description so it can be
    vetoed before merge. If the owner prefers the label to head the whole panel, the honest
    fix is different wording, not a different order.
  - 2026-08-26 — owner asked for three further card-face changes while looking at a live
    metric cell, folded into this branch as the same surface and the same review cycle:
    the metric gloss is now a step larger (0.78rem vs the range labels' 0.72rem), a step
    lighter (--ss-muted vs --ss-caption), and slightly looser (line-height 1.25 -> 1.35 to
    carry the larger size), so the explanation stops competing with the bullet graph's own
    axis furniture. `docs/ui/card_metric_cell.md` records the new typography, since that
    spec documents this element and would otherwise go stale.
  - 2026-08-26 — the owner also asked to drop the "Higher/Lower is better." cue from the
    gloss, then reopened it unprompted, naming the real tension: the claim is only true
    ceteris paribus and this app never teaches that concept. It was removed and then
    RESTORED after discussion. Two things settled it. First, all-or-nothing: a cue present
    on some metrics and absent on others makes its own absence ambiguous, so the
    per-metric split first proposed was wrong. Second, the bar carries no direction of its
    own — right is only "bigger" — so for the benchmarked inverted metrics
    (net_debt_to_ebitda, forward_pe) a beginner cannot read the mark without it, and for
    the 11 of 16 metrics that carry no mark at all it is the only direction signal on the
    card face. (An earlier draft of this reasoning cited current_ratio as a metric whose
    BAR needs the cue; it is `benchmarkable: false` and has no bar. Corrected after
    equity-analyst-reviewer checked the claim against the catalogue rather than taking it.) The clutter complaint was answered in
    presentation instead. Recorded because the code now looks unchanged in this area while
    the decision behind it was genuinely re-taken; do not "clean it up" as dead debate.
