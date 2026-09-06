# Task contract

objective: Close backlog item 3, "the bank card's capital-adequacy blind spot" (owner-flagged
  in `.claude/active_work.md` and `docs/handover_2026-09-03.md`, item 3): financial-type
  (bank) cards only carry the numbers this app can source (profitability and returns), never
  balance-sheet safety or capital strength (CET1/Tier 1 -- unsourceable from yfinance, see
  `docs/data_contract.md`'s "financial" verdict note). Today that limit survives only as an
  instruction inside the LLM prompt (`scripts/assessment_rules.py`'s `READ_SYSTEM_PROMPT`,
  "financial" company-type lens) -- CI pins the instruction's PRESENCE in the prompt text, but
  nothing pins its presence in what the model actually writes, and when `ai_read` is absent
  (pending, a per-card API failure, or a hallucination-guard reject) there is no caveat at
  all. A beginner could read a green "Healthy" badge on a bank stock as "this bank is safe",
  which the app has no way to actually assess.

  This was surfaced to the owner directly (not assumed): explained in plain terms why
  profitability and capital safety are different things for a bank specifically (a bank can
  look profitable right up until it fails on capital adequacy -- the real-world SVB 2023
  collapse was given as a concrete, non-hypothetical example), and why this is the one card
  type where that gap is financially consequential, not just a documentation nicety. Owner
  requested short, easy-to-understand wording and delegated the exact phrasing after that
  context: **"These numbers show profitability only, not whether this bank holds enough
  capital to stay safe."** -- owner-approved verbatim, not self-authored without sign-off
  (§6: user-visible naming/wording is an owner call, every time; this repo's own
  `VERDICT_FALLBACK_READ` comment in `frontend/card_copy.py` states the same rule for this
  exact class of card copy). Superseded by the amendment below -- the final, shipped sentence
  differs from this one.

scope_paths:
  - frontend/card_copy.py (new constant, the owner-approved caveat text)
  - frontend/card_ui.py (`_health_block_html`: render the caveat for financial-type cards)
  - frontend/styles.py (a caption-style CSS rule for the new caveat's class)
  - tests/frontend/test_card_ui.py (new tests)
  - docs/data_contract.md (note the caveat now exists card-face, not just prompt-side)
  - .claude/active_work.md (close out item 3)
  - .claude/task/contract.md
  - .claude/task/review.md

decisions_reserved: none outstanding -- the product decision (does this need a caveat at all)
  and the wording were both put to the owner and answered in this thread, not decided
  unilaterally. One implementation-level choice, disclosed as agent-executable, not
  product content: the caveat renders unconditionally for every financial-type card with a
  known verdict token, regardless of whether `ai_read` is present or absent -- because the
  LLM is only prompted, not required, to mention the limit in its own prose (confirmed by
  reading `READ_SYSTEM_PROMPT` directly: it's a style instruction, not a schema-enforced
  field), so relying on the model to say it every time would reintroduce exactly the gap this
  task closes. This is a placement/reliability decision, not new user-visible wording beyond
  what's already approved above.

done_when:
  - `frontend/card_copy.py`: new module-level constant holding the exact owner-approved
    sentence, placed near `VERDICT_FALLBACK_READ` with a comment explaining why it exists and
    that the wording is owner-authored (matching that constant's own existing comment
    convention). No apostrophe, no em/en dash (same constraint `VERDICT_FALLBACK_READ`'s own
    comment states, since `_esc()`'s HTML-entity-escaping breaks a literal-substring test
    match on those characters) -- the approved wording already satisfies this, verify it
    still does after any transcription.
  - `frontend/card_ui.py`'s `_health_block_html`: the caveat renders inside the existing
    `.ss-health-block` div, after the AI-read-or-fallback narrative, whenever
    `card.get("company_type")` is `"financial"` and a known verdict token is present --
    covering all three narrative states (AI read present; AI read absent with a fallback
    line; AI read absent with no fallback, the current early-return branch). Never shown for
    other company types.
  - `frontend/styles.py`: new caption-style rule (matching the established
    `--ss-caption-size`/`--ss-caption` pattern already used for other secondary/qualifying
    card text, e.g. `.ss-metric-sources`, `.ss-benchmark-unavailable` -- not the same
    equal-weight treatment `.ss-ai-read`/`.ss-verdict-fallback` deliberately share, since this
    is a caveat about the card, not a piece of the narrative itself).
  - `tests/frontend/test_card_ui.py`: new tests confirming the caveat appears for a
    `financial`-type card in all three narrative states above, and confirming it does NOT
    appear for `operating`/`pre_revenue`-type cards even with an identical verdict/ai_read
    shape (the actual regression this task guards against -- a company-type check that
    silently stops firing).
  - Full `pytest` suite green.
  - Mutation-tested: temporarily remove the company_type gate (always render, or never
    render), confirm the new tests actually fail, restore, confirm green again.
  - Manually verified against the running dev server: an actual financial-type card (e.g.
    HSBC or a similar bank already in the deck) shows the caveat; an operating-type card does
    not.
  - `docs/data_contract.md`'s "financial" verdict note updated to mention the caveat is now
    also shown card-face, not just instructed in the prompt.
  - `.claude/active_work.md`: item 3 closed out.
  - No em dash or en dash on any added line.

impact_map:
  - User-visible change: financial-type cards gain one new line of card-face text. No
    verdict/metric computation changes, no data contract change, no new dependency.
  - `frontend/*` and `tests/*` both touched -- per `.claude/review_routing.json`, requires
    cto-reviewer in addition to scope-auditor (`always`). `docs/data_contract.md` also routes
    to equity-analyst-reviewer -- missed in the original impact_map, caught by the commit gate
    itself refusing to commit without that verdict recorded.

amendments:
- scope-auditor (round 1) and cto-reviewer flagged the same fact --
  `.claude/active_work.md` edited but not staged -- and reached opposite verdicts: cto-reviewer
  read it as the session's established convention (`active_work.md`'s own "Review mechanics"
  note: `review.md` + this file are "STILL conventionally committed separately... but this is
  no longer load-bearing... committing it alongside the change it describes works fine too"),
  scope-auditor read `scope_paths` literally and failed it as a gap. Resolved by taking the
  documented "works fine too" option rather than re-litigating the convention: staged
  `.claude/active_work.md` into this same commit. No code or wording changed.
- equity-analyst-reviewer FAILED the owner-approved sentence itself, with evidence independently
  verified before acting on it (not taken on trust): `company_type == "financial"` is the whole
  GICS "Financial Services" sector (`docs/data_contract.md`'s classification note), not
  depository banks -- confirmed against this app's own live S&P 500 constituent data, which
  already includes Visa, Mastercard, BlackRock, Moody's, S&P Global, CME Group, ICE, Chubb,
  Progressive, Allstate, Aon, Marsh McLennan, American Express, and Berkshire Hathaway under
  that sector, none of which are banks. The approved sentence's "this bank" is a factual error
  on all of their cards, and regresses from `scripts/assessment_rules.py`'s own already-shipped,
  already-reviewed `READ_SYSTEM_PROMPT` wording ("this financial company's balance-sheet safety
  or capital strength"), which a prior review already corrected away from the same bank-specific
  over-reach (see that file's `_verdict_financial` comment). Second, smaller finding: financial
  cards also render `revenue_growth_yoy_pct` (`applies_to = operating|financial`, catalogued
  under `growth`, not `profitability`, confirmed in `metric_catalogue.csv`), so "profitability
  only" undersold what the card shows. Both independently confirmed by reading the cited files
  directly, not by trusting the reviewer's claim. Taken back to the owner rather than
  self-corrected (§6): shown the evidence and a proposed fix mirroring the already-reviewed
  `READ_SYSTEM_PROMPT` framing, owner chose the proposed fix as-is. Sentence at that point:
  "These numbers show profitability and returns only, not whether this company holds enough
  capital to stay safe." -- superseded again below, kept here only as the round-2 record.
- A narrow round-3 re-check of that exact sentence (nothing else) FAILED it too, same root
  defect class: `metric_catalogue.csv` shows financial-type cards render four metrics across
  three `perspective` values (`profitability`: `net_margin_pct`; `returns`: `statement_roe_pct`,
  `roa_pct`; `growth`: `revenue_growth_yoy_pct`) -- "profitability and returns only" still
  omitted the growth metric, independently confirmed by querying the CSV directly. Taken back
  to the owner again (§6) rather than patched to a 3-item list and risking a 4th miss later:
  proposed dropping the enumeration entirely and stating only the one fact that's actually
  invariant regardless of which metrics the catalogue carries for this company_type -- capital
  adequacy is never assessed anywhere in this app (confirmed: no metric for any company_type
  measures CET1/Tier 1 or bank-style regulatory capital adequacy; the closest general-leverage
  metrics, `debt_to_equity` and `net_debt_to_ebitda`, are both `applies_to = operating` only and
  explicitly marked meaningless for financials). Owner approved this fix as proposed. Final,
  shipped sentence: **"These numbers do not show whether this company holds enough capital to
  stay safe."** -- confirmed via a further narrow equity-analyst-reviewer re-check to make no
  claim about card contents (so immune to future `metric_catalogue.csv` drift), and confirmed
  its one claim (capital adequacy not assessed) holds unconditionally. This is the sentence
  actually on disk in `frontend/card_copy.py`; both sentences quoted above are superseded.
  "do not", not "don't" -- same no-apostrophe constraint as the others.
- That same round-3 re-check also caught two staleness bugs of my own: `.claude/active_work.md`
  still quoted the round-1 wording (fixed to quote the sentence actually shipped, and its item-3
  heading corrected from "bank card's" to "financial-type card's" to match), and this
  amendments section itself hadn't yet recorded the round-3 approval trail at the moment it was
  checked (fixed by this entry). Both are documentation lag from iterating the wording twice
  more after the round-2 entry was written, not a missing approval -- the round-3 approval
  happened in the same conversation turn that produced this entry.
