# Task contract
> DISPOSABLE. **Owns:** THIS task's objective, `scope_paths`, reserved decisions and
> `done_when`.
> **Never:** anything that outlives the task. Overwritten by the next one.

objective: Make the AI read cite every metric by the label and value the card face shows.
  Issue #9 finding B2.

  Measured: `READ_METRIC_BRIEF` in `scripts/assessment_rules.py` names four of thirteen
  metrics differently from `metric_catalogue.csv` (`Operating margin` for `Operating margin
  (TTM)`, `Revenue growth vs a year ago` for `Rev growth YoY (quarter)`, `Free cash flow
  margin` for `FCF margin (annual)`, `Cash burn per month` for `Cash burn (monthly)`), and
  renders cash runway as `18 months` where the card shows `18.4`. The existing guard checks
  that every input field has a brief, never that the brief agrees with the catalogue.

scope_paths:
  - scripts/assessment_rules.py
  - scripts/generate_assessments.py
  - tests/tooling/test_assessment_rules.py
  - tests/tooling/test_generate_assessments.py
  - docs/data_contract.md
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/active_work.md

decisions_reserved:
  - Which wording wins: owner chose the card's. The read's labels become the catalogue's
    labels verbatim; runway renders as the card does, with "in months" in the gloss so the
    prose can still say what the number is. One card label is per row: operating margin reads
    "(annual)" when the mart fell back to the latest annual statement. "The card's wording"
    means that row's wording, so the read now carries `ebit_margin_basis` and names the metric
    the way `frontend/card_copy.metric_label` does for that row, pinned by test.
  - Regenerating existing reads. Reads regenerate only when a card's input hash moves; a
    prompt-only change leaves stored prose as is until then. Bumping `INPUT_HASH_VERSION`
    would regenerate every read on the next scheduled run, about a thousand Haiku calls;
    that is spend and the owner's call. NOT bumped here. How fast reads converge without a
    bump is unmeasured: the hashed inputs are statement-derived and move when a filing lands,
    so it is per card, not per run. The next scheduled run's `generated` and `carried` counts
    say; the handover carries that check.

done_when:
  - Every `READ_METRIC_BRIEF` label equals the catalogue's `label` for that `metric_id`, and
    a test in `tests/tooling` pins that; operating margin's per-row "(annual)" form is pinned
    against `card_copy.metric_label` through the prompt and the validator.
  - For every catalogued metric and a sample value, `_format_metric_value` in the read
    renders the same string `frontend/card_copy.format_metric_value` renders on the card,
    currency included, and a test pins that.
  - The prose test that asserted `36 months` asserts the card's rendering instead.
  - `docs/data_contract.md`'s AI-read section states that labels and values in the facts
    block are the card's own, pinned by test.

impact_map: Changes the prompt the read model sees, so newly generated reads cite the card's
  labels. Existing stored reads are untouched until their input hash moves. No verdict, hash
  input or card change.
