# Task contract

objective: Fix a ratio sign-inversion problem in the verdict engine, the first point from the
  owner's filed Gemini feedback (`docs/backlog/gemini_verdict_feedback.md`). Two operating-type
  metrics can flip sign when a denominator goes negative, and the verdict currently bands the
  flipped value by raw magnitude, which can read a distressed company as "good" on that axis:
  1. **`debt_to_equity`** -- total debt is never negative in this data, so a negative ratio
     always means negative shareholders' equity. The metric catalogue's own applicability note
     already says so: "heavy buybacks can push equity below zero, and the ratio then flips or
     explodes and stops being meaningful." `card_copy.py`'s display gloss already special-cases
     this ("Negative equity, so this ratio isn't a normal leverage read"); the verdict engine
     does not. (See amendments: shipped as a direct check on equity's own sign, not the ratio's,
     after a review round caught that the ratio's sign is not a reliable tell.)
  2. **`net_debt_to_ebitda`** -- both net debt and EBITDA can independently be negative, so the
     ratio's sign alone can't tell genuine net cash (good) from real debt divided by negative
     earnings (bad, currently mis-banded as good). Telling these apart needs EBITDA's own sign,
     which isn't available to the Python verdict layer today -- only the already-divided ratio
     is passed through. Owner chose the precise fix: expose raw `info_ebitda` end to end so the
     check is exact, not a proxy heuristic.

scope_paths:
  - dbt_analytics/models/4_intermediate/int_stock__card_metrics.sql
  - dbt_analytics/models/4_intermediate/_intermediate.yml
  - dbt_analytics/models/5_marts/mart_stock_cards.sql
  - dbt_analytics/models/5_marts/_marts.yml
  - scripts/assessment_rules.py
  - scripts/generate_assessments.py
  - tests/tooling/test_assessment_rules.py
  - docs/data_contract.md
  - docs/backlog/gemini_verdict_feedback.md
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/active_work.md

decisions_reserved: none for the shape of the fix -- both the approach (guard both metrics'
  verdict banding, not the raw displayed value) and the net_debt_to_ebitda mechanism (precise,
  via a new `info_ebitda` column, not the ebit_margin_pct proxy heuristic) were explicitly
  decided by the owner this session. This DOES change verdicts already shown to users for
  companies matching either pattern -- the owner was told this explicitly before confirming.

done_when:
  - `int_stock__card_metrics.sql` exposes `info_ebitda` AND `stmt_stockholders_equity` as new
    output columns (both already fetched upstream, just not currently passed past the
    intermediate layer). Documented in `_intermediate.yml`, explicitly noted as internal
    verdict-computation signals, not displayed metrics -- neither added to the metric catalogue,
    neither added to the Supabase export list (`scripts/export_to_supabase.py`'s
    `EXPORT_COLUMNS` untouched). `stmt_stockholders_equity` added in a review round (see
    amendments): checking `debt_to_equity`'s own sign missed a debt-free company with negative
    equity (total debt exactly zero divides out to a zero ratio regardless of equity's sign), so
    the guard needs equity's own sign directly, the same reason `info_ebitda` exists for
    `net_debt_to_ebitda`.
  - `mart_stock_cards.sql` passes both columns through too, since `generate_assessments.py`
    reads from this mart, not the intermediate model directly. Documented in `_marts.yml`.
  - `generate_assessments.py`'s `ASSESSMENT_INPUT_COLUMNS` includes both directly (not via
    `INPUT_FIELDS_BY_TYPE`, which specifically means "the full displayed set per type" per its
    own docstring -- neither is displayed nor catalogued).
  - `assessment_rules.py`: one generalized guard function (`_axis_unless_denominator_nonpositive`,
    taking the band to use as a parameter) checks each ratio's raw denominator directly, not the
    ratio's own sign. `net_debt_to_ebitda`'s verdict banding treats itself as `"unknown"` when
    `info_ebitda` is present and `<= 0`. `debt_to_equity`'s verdict banding treats itself as
    `"weak"` (see amendments -- not `"unknown"` as first planned) when `stmt_stockholders_equity`
    is present and `<= 0`. A MISSING denominator does not trigger either guard -- both band
    normally by magnitude, matching every other axis's "missing means unknown, never assumed"
    treatment and, not incidentally, not breaking any existing test (none currently supply either
    new column).
  - `compute_input_hash` needs no separate change: its payload already includes the computed
    `verdict` string directly, so a verdict that changes because of either new guard already
    moves the hash and regenerates the AI-written read, without either new column needing its own
    hash entry.
  - `tests/tooling/test_assessment_rules.py`: new cases proving each guard actually changes an
    outcome (a card that currently reads green/good on the affected axis with a sign-inverted
    value now reads unknown/yellow-at-best), a case per guard confirming a genuinely healthy
    company (real net cash + positive EBITDA; real low debt-to-equity + positive equity) is
    unaffected, a case per guard confirming a MISSING denominator does not trigger it, and a case
    proving `debt_to_equity`'s guard fires on the total-debt-exactly-zero edge case the ratio's
    own sign would miss (`debt_to_equity == 0.0`, `stmt_stockholders_equity` negative).
  - `docs/data_contract.md`'s verdict-rules section gets a short note on both guards, since it's
    the authoritative description of how the color is decided.
  - `docs/backlog/gemini_verdict_feedback.md` updated: point 1 marked acted on, with a pointer
    to this branch.
  - dbt build/test green for both changed models (unit test fixtures for
    `int_stock__card_metrics` may need `info_ebitda` added to their `expect` blocks if the test
    framework requires exact column matching -- verify, don't assume, during Verify).
  - `pytest` green.
  - No em dash or en dash on any added line.

impact_map:
  - Changes verdicts for real cards: any operating-type company with negative shareholders'
    equity, or with `info_ebitda <= 0` (distressed/pre-profit by the catalogue's own words), no
    longer gets a false assist toward green on that specific axis. Some cards currently green
    may move to yellow. Corrected per amendments: the two guards do NOT land the same way --
    `net_debt_to_ebitda`'s move to "unknown" is the neutral, no-worse-than-missing treatment
    every other axis already gets, but `debt_to_equity`'s move to "weak" is deliberately a real
    demotion (a supporting axis in "unknown" never changes anything), so it CAN cap a card at
    yellow that would otherwise have reached green on every other axis.
  - Requires re-running the pipeline (dbt build, then `scripts/generate_assessments.py`) to
    actually recompute verdicts against the fix -- not something `pytest` alone verifies.
  - Known, explicitly out of scope: the AI-written prose read still sees `net_debt_to_ebitda`'s
    raw (possibly sign-flipped) value via its existing metric brief and could describe it
    misleadingly even though the verdict itself is now correct. That's the separately-filed
    "structured AI-read output" backlog point, not fixed here.
  - No frontend change; the card face already shows whatever `net_debt_to_ebitda`/
    `debt_to_equity` value the mart computes, unchanged by this fix (only the internal
    verdict-banding interpretation of that value changes, not the number itself or its
    display).

amendments:
  - Discovered mid-implementation: `debt_to_equity` is a SUPPORTING axis in `_verdict_operating`,
    and supporting axes only affect the card's color when banded `"weak"` (they can block green,
    never rescue it). The plan as written would have banded a negative value `"unknown"` --
    exactly the same treatment supporting axes already tolerate for a genuinely MISSING value --
    which is a no-op on every card's actual color, not the fix described above (some cards
    currently green may move to yellow). Corrected to band `"weak"` instead: negative
    shareholders' equity is a real solvency concern, not a neutral unknown, and `"weak"` gives it
    the same yellow-capping ceiling any other weak supporting axis already has, never forcing red
    on its own, consistent with every other supporting axis in this function. Surfaced to the
    owner before implementing (asked to choose between keeping the no-op version, making it
    count against the card, or dropping the debt_to_equity guard entirely); owner pushed back on
    settling for the no-op as under-scoped work, agreeing with the proposed `"weak"` fix.
  - Round-1 review: equity-analyst-reviewer FAILED the diff with three findings, the other three
    required reviewers (scope-auditor, cto-reviewer, analytics-engineer-reviewer) PASSED. (1)
    `docs/data_contract.md`'s prose calling negative equity "a real solvency concern" overclaimed
    against the catalogue's own applicability note, which attributes it to "heavy buybacks" too
    -- a benign, common pattern among the mature large-caps this app covers, not necessarily
    distress. Fixed: softened to describe `"weak"` as a deliberate caution given the two causes
    can't be told apart, not a claim about which one it is. (2) Real logic gap: checking
    `debt_to_equity`'s own sign misses a debt-free company with negative equity, since
    `stmt_total_debt` (never negative) can be exactly zero, and zero divided by any nonzero
    number is zero, not negative -- such a card would have silently kept banding "good". Fixed:
    added `stmt_stockholders_equity` as a second raw-denominator passthrough (mirroring
    `info_ebitda`) and generalized the one guard function to check either ratio's actual
    denominator, not its sign; new test proves the specific `debt_to_equity == 0.0` edge case is
    now caught. (3) impact_map's blanket "none moves toward a WORSE color" line contradicted this
    same document's amendments section, which explains `"weak"` was chosen BECAUSE it is a real
    demotion `"unknown"` would not have been. Fixed: impact_map corrected above. Also surfaced,
    not fixed here: `statement_roe_pct` (`stmt_net_income_common / stmt_stockholders_equity`) has
    the identical sign-ambiguity problem `debt_to_equity` had, already documented as an accepted,
    unaddressed output by an existing dbt unit test
    (`card_metrics_statement_metrics_negative_equity`); out of this task's confirmed scope, noted
    in `docs/backlog/gemini_verdict_feedback.md` as a likely-direct follow-on since the same
    `stmt_stockholders_equity` column this fix now exposes would drive it too. All four reviewers
    re-run against the corrected diff; see `.claude/task/review.md`.
