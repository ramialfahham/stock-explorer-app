# Task contract
> DISPOSABLE. **Owns:** THIS task's objective, `scope_paths`, reserved decisions and
> `done_when`.
> **Never:** anything that outlives the task. Overwritten by the next task.

objective: The financial-type card's capital-adequacy caveat rendered inside the health
  block, so a card whose block is withheld (no assessment row, or one from another snapshot)
  showed bank metrics with no caveat. Issue #11. Owner chose A: the caveat is its own line
  under the metrics on every financial card, whatever the health block does.

scope_paths:
  - frontend/card_ui.py
  - frontend/card_copy.py
  - frontend/styles.py
  - tests/frontend/test_card_ui.py
  - docs/ui/card_metric_cell.md
  - docs/ui/disclosure_pattern.md
  - docs/data_contract.md
  - tests/frontend/test_styles.py
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/active_work.md

decisions_reserved:
  - Placement, owner-set in chat (option A over B): under the metric stack, inside the
    metrics section, on every financial-type card. The wording
    (`FINANCIAL_CAPITAL_ADEQUACY_CAVEAT`) is unchanged.
  - Styling reuses the existing caption treatment; only the selector's scope and a top
    margin change. No new token.

done_when:
  - `_financial_caveat_html(card)` returns the caveat for `company_type == "financial"`
    and "" otherwise; `build_card_html` appends it after the metric grid inside
    `.ss-card-metrics`; `_health_block_html` no longer emits it.
  - Tests over `build_card_html`: a financial card shows the caveat exactly once, after the
    metrics section starts and outside the health block, in four states (AI read, fallback
    read, no verdict, bare card); operating and pre-revenue cards never show it; with a
    folded read the caveat comes after `</details>`. The four-state test fails against HEAD.
  - `docs/ui/card_metric_cell.md` specifies the line; `docs/ui/disclosure_pattern.md` and
    `docs/data_contract.md` (the financial verdict entry and the withheld-block paragraph)
    no longer say the caveat is in the block; the `card_copy.py` and `card_ui.py` comments
    that recorded issue #11 as a known gap describe the new placement.
  - `tests/frontend/test_styles.py` pins the caveat rule to `.ss-card-metrics`, so a revert
    of the selector cannot leave the line unstyled unnoticed.
  - UX gate: 480px render of both states checked in the browser (one caveat each, under
    the last metric, no horizontal scroll); first metric above the fold unaffected because
    the line sits below the stack.
  - `pytest tests/ -q` green.

impact_map: Card face HTML for financial-type cards only (one `<p>` moves from the health
  block to the metrics section); one CSS rule rescoped. No data, no dbt, no export change.
