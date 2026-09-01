# Task contract

objective: Record a decision on Gemini feedback point 9 (sector/size threshold calibration,
  `docs/backlog/gemini_verdict_feedback.md`) -- considered, not pursued. Documentation only, no
  verdict-logic change. Investigated whether the fixed, per-`company_type` verdict thresholds in
  `scripts/assessment_rules.py` should be calibrated by sector and/or company size, as Gemini's
  point 9 suggested and as candidate direction 3 in the backlog doc flagged as "the largest of
  the set, warranting its own scoping pass." Owner asked explicitly not to hallucinate a
  proposal, and was openly skeptical anything less arbitrary than the status quo exists.

  Findings that led to the decision:
  - The current fixed thresholds are not actually arbitrary: `net_debt_to_ebitda` good/weak at
    1.5x/3x mirrors common leverage credit-quality bands (rating-agency-style "low"/"aggressive"
    tiers, not a specific loan covenant, which typically sits higher, around 4x-6x, for
    leveraged borrowers); `ebit_margin_pct` good at 10% is a standard double-digit-margin
    heuristic; `current_ratio_stmt` good/weak at 1.5/1.0 is classic textbook liquidity
    convention; `cash_runway_months` good/weak at 24/12 months is a standard startup-finance
    heuristic. The premise that they need fixing doesn't hold up.
  - `docs/north_star.md` already has an owner-signed rule for a closely related feature (the
    display benchmark, not the verdict): "Do not use naive 'Top 10% in sector' rankings --
    misleading for debt, negative growth, etc." The same risk applies to verdict-threshold
    calibration: a mediocre company in a sector currently having a bad run would read green
    purely because its peers are worse, contradicting the AI-read's own closing claim,
    "financially healthy on these figures" -- an absolute claim, not a relative one.
  - Sector-relative comparison is a real, standard practice in equity analysis (margin and
    leverage norms genuinely differ by industry structure). Size-adjusted THRESHOLDS are not --
    real credit/fundamental analysis handles issuer size through business-risk-profile overlays
    that typically TIGHTEN expectations for smaller, less-diversified issuers to hold the same
    rating, not through loosening what counts as a healthy margin or leverage ratio for a
    small-cap, so any size-bucket cutoffs here would run backwards from how size is actually
    treated. Either way, exactly the kind of invented number the owner was concerned about, with
    no real convention to anchor it to.
  - Practical cost, independent of the above: sector medians shift on every biweekly pipeline
    refresh, and the display feature's own 8-peer minimum shows how thin these peer groups can
    get, so a company's verdict could flip color with none of its own numbers changing -- a
    stability problem for a tool whose value is a transparent, deterministic rule.
  - This declines the specific mechanism point 9 proposed (the mart's live `sector_median`/
    `min`/`max`, recalculated every refresh -- the same live-curve pattern `north_star.md`'s
    existing rule already warns against), not every conceivable version of sector awareness. A
    structurally different alternative -- deliberately set, externally-anchored per-sector
    benchmark tables revised on a deliberate cycle rather than a live refresh -- would sidestep
    the instability concern while still respecting genuine sector-driven differences. Worth
    naming as the version to scope if this is ever revisited, not something this decision
    forecloses.

  Decision: do not calibrate verdict thresholds by sector or size. Close point 9 in the backlog
  doc as considered and declined, with this reasoning recorded for anyone who revisits it later.

scope_paths:
  - docs/backlog/gemini_verdict_feedback.md
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/active_work.md

decisions_reserved: none remaining -- this contract records the decision itself, already made by
  the owner this session after the owner's own explicit skepticism was investigated and
  confirmed rather than talked past. No verdict rule, threshold, or code changes; nothing here
  changes any already-shipped output.

done_when:
  - `docs/backlog/gemini_verdict_feedback.md` point 9's Context entry gets a "Considered, not
    pursued" note with the reasoning above.
  - Candidate direction 3 (sector/size threshold calibration) marked declined, not "Done", with a
    pointer to point 9's entry for the reasoning -- this is the first candidate direction this
    session that resolves to "don't build it" rather than "acted on", and the doc's phrasing
    should make that outcome as visible as an "Acted on" one, not buried.
  - The "Open questions" entry asking whether sector/size calibration fits the app's stated
    design at all gets answered, pointing at the same reasoning.
  - No em dash or en dash on any added line.

impact_map:
  - No functional change of any kind -- documentation only. No verdict output changes, no
    pipeline re-run needed, no test changes (nothing in `scripts/`, `tests/`, or `dbt_analytics/`
    is touched).
  - Closes out the last unaddressed Gemini-feedback point from this session's candidate-direction
    list that had a real decision pending (points 2, 3/4, 5 remain genuinely open, not yet
    raised with the owner this session).

amendments: (none)
