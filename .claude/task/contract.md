# Task contract
> DISPOSABLE. **Owns:** THIS task's objective, `scope_paths`, reserved decisions and
> `done_when`.
> **Never:** anything that outlives the task. Overwritten by the next one.

objective: The learn panel's four practice playgrounds follow the card face: only the
  metrics the face shows for this card get a playground, each carries the face's label,
  and money inputs carry the card's currency. Issue #9 finding B1.

scope_paths:
  - frontend/metric_school.py
  - frontend/card_copy.py
  - scripts/audit_mart_vs_yfinance.py
  - docs/metric_audit.md
  - docs/backlog/landing_onboarding_rework.md
  - tests/frontend/test_metric_school.py
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/active_work.md

decisions_reserved:
  - Keep the playgrounds. The finding lists three user-visible consequences to fix, not the
    feature's existence; `docs/north_star.md` names the playgrounds as part of the learn
    panel. Removing them is the owner's alternative (product content, §6), recorded, not
    taken.
  - The playground arithmetic stays in Python. It teaches the catalogue's `calculation`
    sentence on numbers the user types; no stored value on any card comes from it. The
    invariant in `scripts/audit_mart_vs_yfinance.py` is reworded to what it guards (no
    Python path produces a card value), because as written it was false of the repo.
  - Input wording: "Revenue ($B)" becomes the same words with the card's currency symbol,
    as `format_metric_value` already prints money on the face. The words themselves are
    unchanged; the owner may reword.

done_when:
  - A pure `playgrounds_for_card(card)` returns the ordered playground metrics that are in
    `metrics_for_card(card)`; `render_metric_playgrounds` renders exactly those tabs and
    nothing when the list is empty. Tests: an operating card with all four values gets four;
    a financial card gets only revenue growth; a pre-revenue card gets none; a card missing
    one value loses that tab.
  - Tab and heading labels come from `metric_label(metric, card)`, so an `annual_latest`
    card's margin playground reads "Operating margin (annual)" like its face.
  - Money inputs carry the card's currency symbol through a public `currency_symbol()` in
    `card_copy`, which `_format_currency_compact` also uses; unit test pins a GBP label, a
    symbol-less code and the no-currency fallback.
  - An AppTest renders `render_metric_playgrounds` for an operating GBP `annual_latest` card
    (four tabs in face order, first tab "Operating margin (annual)", eight inputs all ending
    "(£B)"), a financial card (one tab, two inputs) and a pre-revenue card (nothing), so the
    dispatch, the tab labels and the input labels are executed by a test.
  - The `METRIC_LABELS[...]` scan test is replaced by one over the playground registry
    (every registered metric is in the catalogue).
  - `scripts/audit_mart_vs_yfinance.py` docstring and `docs/metric_audit.md` state the
    invariant as what holds: no Python path produces a stored metric.
  - `pytest tests/ -q` green.

impact_map: `frontend/metric_school.py` (render path and a new pure selector),
  `frontend/card_copy.py` (one public helper over the existing symbol table),
  `scripts/audit_mart_vs_yfinance.py` and `docs/metric_audit.md` (invariant wording). No dbt,
  no mart, no catalogue change.
