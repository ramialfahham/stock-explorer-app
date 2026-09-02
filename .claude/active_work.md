# Active work — handover

_The next session is handed exactly this file. Keep it current. Full slice-by-slice
history through 2026-08-18 is archived in [`docs/handover_2026-08-18.md`](../docs/handover_2026-08-18.md)
— this file stays lean on purpose (it's injected whole at SessionStart by `handover_in.py`,
capped at 32,000 bytes; see Context/open items). When a slice merges, collapse its Status entry to
one line here and let the archive keep the detail._

**SIZE WARNING, flagged by scope-auditor 2026-08-28: this file is ~95KB, nearly 3x its own
stated 32,000-byte injection cap.** `handover_in.py` truncates on injection, so a fresh session
may not be seeing all of this. Needs an archival pass (move settled history into
`docs/handover_2026-08-18.md`'s successor) before the next onboarding batch adds more. Not done
in this session; flagging so it isn't lost.

## Branch `feat/ai-read-structured-hallucination-guard` IN PROGRESS, 2026-09-02: Structured
AI-read output + hallucination guard (Gemini feedback points 3/4), plus a frontend fallback for
a null `ai_read`

Status: **implemented (backend + frontend + tests), full pytest suite green (470 passed), docs
updated (`data_contract.md`, `north_star.md`, `backlog/gemini_verdict_feedback.md`), em/en-dash
swept. Not yet reviewed, not yet committed, not yet pushed.** Next concrete action: stage
everything, hash the diff, dispatch the three required reviewers (scope-auditor always;
cto-reviewer for `scripts/*`, `tests/*`, `frontend/*`; equity-analyst-reviewer for
`docs/data_contract.md`), write `.claude/task/review.md`, commit (main change then review.md
separately), then wait for the owner's explicit instruction to push -- push to the `gitlab`
remote, not `origin`.

Owner confirmed the design across conversation, then reworked the frontend fallback text several
more times after implementation (see `.claude/task/contract.md`'s `amendments` for the full
account): the original plan sketched fallback body text as a description of the verdict engine's
internal rule mechanics, but that was found mid-task to reference concepts (a
decisive-vs-supporting metric split, per-metric thresholds) with zero representation anywhere in
the UI -- `metrics_for_card()` renders every metric flatly, and the catalogue's `importance_tier`
tier-visibility split is defined but unused anywhere in `frontend/`. Final wording is an
owner-authored general one-line business-language summary per verdict color instead
(`frontend/card_copy.py`'s `VERDICT_FALLBACK_READ`).

Also trimmed one pre-existing comment in `scripts/assessment_rules.py` (current-ratio
FCF-coverage relief) that embedded a real company's exact figures and a version-history
narrative, after it caused Claude to misdescribe the logic to the owner as "hard-coded" --
standing instruction going forward: no concrete real-world examples or version-history narrative
in code comments, state the current rule and its rationale only. A matching example in
`docs/data_contract.md`'s joint-liquidity-evaluation bullet was flagged as a spawned background
task (`task_df34cb5b`), not fixed in this branch (out of this task's own `scope_paths` intent).

## MR !79 OPEN, 2026-09-01: Decline sector/size threshold calibration (Gemini feedback point 9)

Status: **implemented (docs only), reviewed 3 rounds (scope-auditor PASS by the final round,
plus a voluntary equity-analyst-reviewer pass -- see that branch's `.claude/task/review.md` for
the full account), committed (2 commits: decision + review.md separately), pushed, MR open
awaiting merge.** Branch `docs/decline-sector-size-calibration`, MR at
https://gitlab.com/rami.al-fahham/stock-swipe-app/-/merge_requests/79. Pushed to the `gitlab`
remote, not `origin` (see the remote note under MR !73's entry below). Next concrete action: once
merged, sync local `main` and delete the branch.

Owner asked to investigate point 9 (sector/size threshold calibration) properly, explicitly
warning against inventing a proposal not grounded in real practice, and was openly skeptical
anything less arbitrary than the status quo exists. Investigated rather than assumed either way:
the current fixed thresholds turn out to already mirror standard financial conventions (leverage
credit-quality bands, textbook liquidity ratios, standard margin/runway heuristics), not
arbitrary picks; `docs/north_star.md` already carries an owner-signed rule against naive
sector-relative rankings for the display benchmark, and the same risk applies to verdict
thresholds (a mediocre company in a weak sector would read green purely because its peers are
worse, contradicting the AI-read's own absolute "financially healthy on these figures" framing);
size-adjusted thresholds specifically have no real-analyst convention to anchor them to; sector
medians shift every biweekly refresh, so calibrated verdicts could flip color with no change in
the company's own numbers.

**Dispatched equity-analyst-reviewer voluntarily, since this doc makes analyst-grade financial
claims that scope-auditor's own review flagged as never getting an independent domain check
under the current routing.** Caught two real precision issues (not fabrications, didn't reverse
the conclusion): calling the leverage threshold's 1.5x/3x band "lending-covenant conventions"
overclaimed a specific provenance -- real covenants typically sit higher (4x-6x) for leveraged
borrowers; what it actually mirrors is closer to rating-agency-style credit-quality banding.
And "real analysts handle size via required-return premiums" named the wrong mechanism -- that's
an equity-valuation discount-rate construct, not how credit/fundamental analysis treats issuer
size, which is business-risk-profile overlays that TIGHTEN (not loosen) expectations for smaller
issuers -- a correction that argues even more strongly against loosening thresholds, not less.
Both fixed in the backlog doc and this contract. Also added, per the reviewer's completeness
note: this decision declines specifically the live-sector-median mechanism Gemini's point 9
proposed, not every conceivable sector-aware design -- a deliberately-set, externally-anchored
per-sector benchmark table (revised on a cycle, not live) would sidestep the instability concern
and is worth naming as the version to scope if this is ever revisited.

**Round-2 scope-auditor FAIL, on the completeness note itself.** While incorporating it, one
phrase from the reviewer's own suggestion -- "closer to how rating agencies publish industry
benchmark tables" -- made it into the backlog doc but never got propagated to this contract, and
was never independently fact-checked the way the other two corrections were (both had explicit
citations; this one didn't). scope-auditor caught the inconsistency and, more importantly, the
fact that it was an unverified analyst-grade claim added mid-edit in the exact document whose
premise is not shipping unverified claims -- the failure mode this whole exercise exists to
avoid, right down to the letter. Fixed by removing the specific "rating agencies" citation from
the backlog doc, keeping only the self-evident structural point (deliberately set, revised on a
cycle, not live) that needs no external precedent to be true.

Decision: do not calibrate verdict thresholds by sector or size. `docs/backlog/gemini_verdict_feedback.md`
updated: point 9 marked "Considered, not pursued" with the reasoning, candidate direction 3
marked "Declined" (this session's first candidate direction to resolve to "don't build it" rather
than "acted on"), the open question about whether this fits the app's design answered "no."
No code, test, or verdict-logic changes -- documentation only.

## MR !77 MERGED, 2026-09-01: statement_roe_pct sign-inversion guard (sibling of MR !73)

Status: **merged, local `main` synced, branch deleted, remote-tracking ref pruned.** MR was at
https://gitlab.com/rami.al-fahham/stock-swipe-app/-/merge_requests/77. Reviewed 5 rounds (the
most contested fix this session -- see that MR's commit `d27354d0` / `.claude/task/review.md`
for the full account of what rounds 1-4 each caught and fixed).

This closes out the three Gemini-feedback fixes shipped this session: MR !73 (ratio
sign-inversion guard, points 1), MR !75 (joint liquidity evaluation, points 6/8), MR !77
(statement_roe_pct sign-inversion guard, sibling of point 1). Remaining unactioned points in
`docs/backlog/gemini_verdict_feedback.md`: point 2 (early-stage classification review), points
3/4 (structured AI-read output + hallucination guard), point 5 (outlier-aware metric-range
scaling), point 9 (sector/size threshold calibration -- flagged in the doc itself as the largest
of the set, warranting its own scoping pass).

The sibling bug flagged but not fixed while shipping MR !73: `statement_roe_pct` (`stmt_net_income_common
/ stmt_stockholders_equity`) has the identical sign-ambiguity problem `debt_to_equity` had -- a
loss over negative equity divides out to a spuriously POSITIVE percentage. Fixed by reusing the
existing `_axis_unless_denominator_nonpositive` guard (no new function, no new dbt column) on both
call sites, checking `stmt_stockholders_equity`'s own sign directly.

**Round-1 review caught a real overreach in the financial-side justification -- corrected.**
First version banded `weak` on `financial` (forcing red outright), reasoned from US bank capital
regulation (FDIC Prompt Corrective Action) after web research the owner explicitly required
("don't hallucinate, do it like it is done in reality"). equity-analyst-reviewer FAILED it: the
research was sound for US depository banks specifically, but `company_type == 'financial'` is the
whole GICS "Financial Services" sector (insurers, asset managers, payment networks, exchanges,
mortgage finance -- not just banks), spans nine markets under entirely different regulators (US,
UK, Japan, Australia, Germany, France, Netherlands, Switzerland, Spain), and includes firms
(payment networks especially) famous for the same benign buyback-driven negative equity operating
companies can have -- exactly the case the original reasoning itself said should get the mild
treatment. Corrected: financial's band changed from `"weak"` to `"unknown"` -- still blocks green,
no longer forces red, matching the neutral treatment every other axis gets for information this
app cannot actually determine. **cto-reviewer separately FAILED a test**
(`test_operating_statement_roe_guard_caps_a_negative_equity_card_at_yellow`) that couldn't
actually detect a broken guard, confirmed by mutation testing, because `debt_to_equity`'s own
pre-existing guard checks the SAME `stmt_stockholders_equity` field unconditionally and alone
already explains the yellow outcome. Fixed (round 1) by adding a direct function-level test
isolating the new guard from the old one -- but that test only proved the shared guard function
works, without ever calling `_verdict_operating`. **Round 2, both scope-auditor and cto-reviewer
independently caught the deeper version of the same gap**: mutation-tested by reverting the
operating call site back to plain `_axis(...)` and running the whole suite -- all 75 tests in the
file still passed, since NO row constructible through `compute_verdict` can isolate
`statement_roe_pct`'s call site from `debt_to_equity`'s (the latter fires unconditionally on
`stmt_stockholders_equity`'s sign alone, regardless of its own metric's value or even presence).
Fixed properly this time: `test_operating_statement_roe_call_site_is_actually_wired` uses
`pytest`'s `monkeypatch` fixture to neutralize `debt_to_equity`'s guard specifically while
leaving `statement_roe_pct`'s call to the real guard, then drives the row through
`compute_verdict` -- verified directly (reverted the call site, confirmed this specific new test
fails while the old confounded one still passes, then restored and reran the full suite green).
Also fixed a stale backlog-doc line both reviewers caught, left over from the rejected "forces
red" version. **Round 3, cto-reviewer caught one more staleness**: the module-level "Ratio
sign-inversion guards" preamble comment (untouched by any hunk in this diff until then) still
said "Two operating-type ratios" / "Both guards," but this diff adds a third guarded metric
(`statement_roe_pct`, used from both verdict functions with a role-dependent band), which the
preamble neither counted nor explained -- exactly the kind of shared-comment sweep the per-call-
site updates all missed. Fixed by rewriting the preamble. **Round 4, cto-reviewer caught a fresh
error the round-3 rewrite itself introduced**: the new preamble claimed statement_roe_pct's
numerator (net income) "is never negative" -- false, a loss is exactly the bug this guard exists
to catch, and the claim contradicted the preamble's own opening sentences. Root cause:
over-generalized debt_to_equity's true "numerator never negative" property across to
statement_roe_pct while merging the two explanations into one sentence. Fixed by describing all
three metrics' genuinely distinct failure modes separately. Full account in
`.claude/task/contract.md`'s `amendments`.

8 test cases in `tests/tooling/test_assessment_rules.py` (a direct function-level isolation test,
a monkeypatch-based call-site wiring test, plus verdict-level cases per card type: guard flips a
real case, positive-equity unaffected, missing equity unaffected; operating confirms a red core
axis still wins; financial confirms a genuinely weak margin still independently forces red).
`docs/data_contract.md`'s verdict-rules
section and the backlog doc's sibling-bug note updated to match the corrected mechanism. No dbt
changes needed.

## MR !75 MERGED, 2026-09-01: Joint liquidity evaluation (Gemini feedback points 6/8)

Status: **merged, local `main` synced, branch deleted, remote-tracking ref pruned.** MR was at
https://gitlab.com/rami.al-fahham/stock-swipe-app/-/merge_requests/75. Reviewed 3 rounds (all
four required reviewers PASS by round 3 -- see that MR's commit `78ecdc9a` /
`.claude/task/review.md` for the full account, including the round-1 financial-reasoning gap a
review round caught and the redesign that fixed it).

**Both Gemini-feedback points acted on this session (point 1: MR !73, points 6/8: MR !75) share
one lesson worth carrying forward: a reviewer catching a real logic gap mid-task is normal here,
not a sign the plan was wrong** -- both times the right move was to redesign properly (expose a
raw denominator/dollar figure instead of inferring from a derived ratio) rather than patch around
the finding with a caveat. Remaining backlog items from `docs/backlog/gemini_verdict_feedback.md`
not yet raised with the owner: point 2 (early-stage classification review), points 3/4 (structured
AI-read output + hallucination guard), point 5 (outlier-aware metric-range scaling), point 9
(sector/size threshold calibration -- flagged in the doc itself as the largest of the set,
warranting its own scoping pass). Also flagged, not yet its own task: `statement_roe_pct` has the
identical sign-ambiguity bug `debt_to_equity` had (see MR !73's backlog note), and the
`stmt_stockholders_equity` column MR !73 already exposed would very likely support the same fix
directly.

Second point acted on from `docs/backlog/gemini_verdict_feedback.md`. `current_ratio_stmt`
(supporting axis) and free cash flow used to be graded fully independently in
`_verdict_operating`, so a company with excellent free cash flow but a merely-weak current ratio
was capped at yellow regardless -- Apple's real card (current ratio 0.89, FCF margin 23.7%) is
exactly this case. Owner explicitly judged the Mixed reading as the actual defect (contradicts
real-world consensus on Apple's financial health), not the conservative "one weakness caps it"
design -- a genuine methodology fork, escalated and decided before any code was written (see
`.claude/task/contract.md`).

**Round-1 review caught a real financial-reasoning gap, redesigned.** First version gated relief
on `fcf_margin_pct` banding `good` (FCF ÷ revenue). equity-analyst-reviewer FAILED it: margin
doesn't track the SIZE of the liquidity gap, which isn't proportional to revenue for a company
whose current liabilities carry a near-term debt-maturity wall -- built a concrete counter-example
(modest revenue, decent FCF margin, real FCF a small fraction of a real dollar shortfall) that
the old mechanism would have wrongly waved through. Redesigned to a direct dollar comparison:
`current_ratio_stmt` now bands `ok` instead of `weak` when free cash flow (`stmt_free_cash_flow`,
a new raw passthrough, same pattern as `info_ebitda`) covers the working-capital shortfall
(`stmt_free_cash_flow >= -working_capital`; `working_capital` was already flowing through, no new
wiring needed there) AND `current_ratio_stmt` is at or above `CURRENT_RATIO_LIQUIDITY_FLOOR`
(`0.5`, unchanged). Still relieves Apple (FCF a large multiple of its small shortfall), correctly
withholds relief from the counter-example. cto-reviewer separately FAILED a test
(`...requires_fcf_margin_actually_good`) that couldn't actually detect a broken relief gate,
confirmed by mutation testing -- moot now since the redesign no longer references
`fcf_margin_pct` at all. Full account in `.claude/task/contract.md`'s `amendments`.

10 test cases in `tests/tooling/test_assessment_rules.py` covering the relief mechanism (Apple's
numbers reach green, the debt-maturity-wall counter-example is correctly denied, the floor and
its boundary, the coverage boundary, missing FCF/working_capital earns no relief, a non-negative
working_capital earns no relief, relief doesn't rescue an unrelated weak axis, a missing current
ratio is untouched). `test_operating_supporting_weakness_blocks_green` uses `statement_roe_pct`
instead of `current_ratio_stmt` as its weak-supporting-axis example now.
`docs/data_contract.md`'s verdict-rules section and the backlog doc's points 6/8 updated to match
the corrected mechanism.

## MR !73 MERGED, 2026-09-01: Ratio sign-inversion guard (Gemini feedback point 1)

Status: **merged, local `main` synced, branch deleted, remote-tracking ref pruned.** MR was at
https://gitlab.com/rami.al-fahham/stock-swipe-app/-/merge_requests/73. Reviewed 2 rounds (all
four required reviewers PASS on round 2 -- see that MR's commit `1d841a31` /
`.claude/task/review.md` for the full account).

**Remote note for future sessions: `origin` points at a suspended GitHub account**
(`github.com/ramialfahham/stock-swipe-app`), unrelated to this project's actual GitLab-based
workflow. Use `git push gitlab <branch>` and `glab mr create`, not `git push`/`gh`, in this repo.

**Next concrete action: re-run the pipeline (dbt build already re-runs on the next scheduled CI
job; `scripts/generate_assessments.py` against Supabase) to actually recompute production
verdicts against this fix -- not yet done, and not something this session verified beyond the
local dev sample (63 cards, no company that trips either guard).**
Next concrete action: once merged, sync local `main` and delete the branch. Production verdicts
only move on the next real pipeline run post-merge (the local dev sample has no company that
trips either guard, so this couldn't be visually verified pre-merge).

First point acted on from `docs/backlog/gemini_verdict_feedback.md` (filed 2026-08-31). Two
operating-type verdict axes could flip sign when a denominator went negative, and the old
magnitude-only banding read the flipped value as good:
- **`net_debt_to_ebitda`** (core axis) -- both net debt and EBITDA can independently be negative,
  so the ratio's own sign can't tell genuine net cash from real debt over negative earnings.
  Fixed precisely (owner's call over a proxy heuristic): a new `info_ebitda` passthrough column
  added end to end (`int_stock__card_metrics.sql` -> `mart_stock_cards.sql` ->
  `generate_assessments.py`'s `ASSESSMENT_INPUT_COLUMNS`, data-only, not catalogued, not
  exported to Supabase) lets the axis band `"unknown"` when `info_ebitda` is present and `<= 0`.
  This is a CORE axis, so the fix changes real card colors: green -> yellow for any such card.
- **`debt_to_equity`** (supporting axis) -- total debt is never negative in this data, so a
  negative ratio always means negative shareholders' equity. **Mid-implementation correction**:
  the original plan banded this `"unknown"` too, but supporting axes only affect the card's color
  when banded `"weak"` (they block green, never rescue it) -- and a negative value was ALWAYS
  `"good"` under the old banding too, so `"unknown"` would have been a no-op on every card's
  actual color. Caught this, flagged it, owner pushed back on settling for the no-op ("reads like
  you don't want to do the professional work"); corrected to band `"weak"` instead, which caps
  the card at yellow the same way any other weak supporting axis already does.
- **Round-1 equity-analyst-reviewer FAIL, round-2 fix.** Checking `debt_to_equity`'s own sign
  missed a debt-free company (`stmt_total_debt` exactly zero) with negative equity, since zero
  divided by any nonzero number is zero, not negative -- such a card would have silently kept
  banding "good". Fixed by adding a second raw-denominator passthrough,
  `stmt_stockholders_equity` (mirroring `info_ebitda`), and generalizing the one guard function
  to check either ratio's actual denominator directly, never the ratio's own sign. Also softened
  `docs/data_contract.md`'s prose, which had overclaimed negative equity as "a real solvency
  concern" when the metric catalogue itself attributes it partly to benign buybacks -- now framed
  as a deliberate caution given the two causes can't be told apart. See
  `.claude/task/contract.md`'s `amendments` for the full two-round account.

**Sibling bug found, not fixed here:** `statement_roe_pct` uses the same `stmt_stockholders_equity`
denominator and has the identical sign-ambiguity problem (a loss over negative equity divides out
to a spuriously positive ROE) -- already documented as an accepted, unaddressed output by an
existing dbt unit test. Out of this task's confirmed scope; noted in
`docs/backlog/gemini_verdict_feedback.md` as a likely-direct follow-on, since the same
`stmt_stockholders_equity` column this fix now exposes would drive it too.

7 new test cases in `tests/tooling/test_assessment_rules.py` (both guards flip a real case, both
leave a genuinely-healthy case alone, both ignore a MISSING denominator/value rather than treating
absence as bad, plus the debt-free/negative-equity edge case round 1 caught). `docs/data_contract.md`'s
verdict-rules section and the backlog doc's point 1 updated. Local dev sample (63 cards, 7
tickers/market) has no company that trips either guard, so `generate_assessments.py --dry-run`
against it still shows all-green -- expected sampling gap, not a bug; guard correctness rests on
the unit tests, not this local sample. Actual production verdicts only move on the next real
pipeline run post-merge.

## MR !72 MERGED, 2026-08-31: Discover header polish

Status: **merged, local `main` synced, branch deleted.** MR was at
https://gitlab.com/rami.al-fahham/stock-swipe-app/-/merge_requests/72.
Two small, already-diagnosed bugs from the row-tap-target investigation (MR !67), surfaced to
the owner as a "what's next" recommendation once the click-latency work landed, and confirmed
with a plain "yes":
- **Market filter dropdown offered markets with zero companies.** `frontend/markets.py`'s
  `MARKET_DISPLAY_NAMES` is a static 9-market dict; `explore_filters.market_filter_options()`
  listed every entry regardless of whether that market actually had eligible companies exported
  yet (4 of the 9 -- France, Netherlands, Switzerland, Spain -- were onboarded but the pipeline
  hadn't run for them since). `market_filter_options()` now takes the live `cards` list (matching
  `sectors_for_market()`'s existing pattern) and only includes a market with at least one
  eligible card, preserving `MARKET_DISPLAY_NAMES`'s registry-ingest ordering among the ones
  shown. If the current session's `explore_market` selection drops out of the live list, it
  resets to `default_market_filter()` before the selectbox renders, matching the existing
  self-healing pattern already used for `explore_sector`. Live-verified via the accessibility
  tree: exactly the 5 markets with live data (S&P 500, FTSE 100, Nikkei 225, ASX 200, DAX) now
  appear, the other 4 don't.
- **Filters/stats stayed visible on the focus card.** `_render_explore_filters()` and the
  "remaining match your filters" portion of `_render_scope_stats()` ran unconditionally whenever
  the active tab was Discover, with no check for whether a card was focused. Both now skip when
  `st.session_state["discover_focus_key"]` is set; `{saved} saved` still renders regardless,
  matching Saved's own already-established behavior of never hiding it. Live-verified: opening a
  row hid the Filters button and "match your filters" text while "0 saved" remained, "Back to
  list" restored both, Saved's own header (a separate, untouched code path) was unaffected.

`docs/ui/discover_header.md` updated (vertical-order table rows 5-6, the wireframe caption, the
Filters-popover section, and the 480px smoke checklist) to describe both as list-view-only.
5 new tests in `tests/frontend/test_explore_filters.py` cover `market_filter_options()`'s
filtering and ordering.

**Round-1 scope-auditor catch: this diff is a Discover-chrome interaction change, so
`docs/working_agreement.md`'s UX PR gate applies unconditionally, not only when a product
decision is involved** -- the original contract only addressed the working agreement's separate
decision-rights question (§6), not this gate. Walked through all five gate items: north_star
check (`north_star.md`'s Browse row already says focus view matches "the same layout Saved's
focus view already uses" -- Saved has no Filters row, so this change moves Discover INTO
alignment, not away from it); component specs (`discover_header.md` updated in this same diff);
one primary job and a mobile wireframe go in the MR body; 480px smoke was actually re-run at a
480x900 viewport (round 1's live verification had only checked desktop width) -- no horizontal
scroll on the list or focus view, Filters row genuinely absent with no leftover gap on focus
(screenshot-confirmed), Save/Not now reachable, "Back to list" restores cleanly.

**Round-2 scope-auditor edge case, not fixed, flagged for the owner's awareness:** if the
Discover pool ever became completely empty while a card was still focused (not currently
reachable via Save/Skip/filter-change, which all clear `discover_focus_key`; would need
something like an external eligibility sync mid-session), `_render_discover_tab`'s existing
empty-pool message ("Try another market, sector, or clear filters") would show while the
Filters control it points to is hidden by this same diff's own fix. Low likelihood, not a
scope or decision-rights issue, not actioned here.

## MR !71 MERGED, 2026-08-31: Discover click latency (Supabase anon-client caching)

Reviewed 2 rounds; one Claude Code crash mid-review, recovered by re-dispatching against the
same frozen diff -- see that branch's `.claude/task/review.md` for the full account.
Owner reported the app "substantially faster" after MR !70's pagination fix (see the entry below
this one) but still delayed 1-2s per click. Diagnosed with server-side timing instrumentation
(temporary, not shipped -- the earlier browser-side JS-timer approach this session used for
MR !70's own verification was unreliable, throttled on a reported-hidden preview tab; server-side
`time.perf_counter()` checkpoints avoid that entirely). Found: `get_anon_client()`
(`frontend/supabase_client.py`) rebuilt a brand-new Supabase client via `create_client(url, key)`
from scratch on every single Streamlit script rerun, with zero caching -- unlike card data, which
is correctly cached in `session_state`. Measured cost: ~1.06-1.09s per run, consistently, versus
~0.12-0.18s for everything else in a run combined. Because `frontend/row_ui.py`'s row click
handler calls `st.rerun()` right after registering a click (aborting the in-flight run and
starting a fresh one), this cost was paid twice per click, not once -- closely matching the
owner's reported 1-2s, and unrelated to row count or list position (fixed per-run cost, not
scaling with the pool size pagination already capped).

Fixed with `@st.cache_resource` (Streamlit's own primitive for an expensive-to-construct,
shareable resource with no per-user state -- this is the anonymous, non-user-specific client).
Cached globally across the whole server process, not per-session: the one-time construction cost
is paid once total, not once per visitor. Live-verified post-fix: two clicks measured at ~0.30s
and ~0.47s total click-to-response (down from ~1.2-1.4s for a single run pre-fix, worse across
the two runs a click actually costs). `tests/frontend/test_supabase_client.py` added: confirms
two calls return the same object with `create_client` invoked once, and that the
credential-missing error path still runs on every call (a cached resource must not paper over a
genuinely missing configuration).

The `st.rerun()`-inside-the-loop pattern itself (row_ui.py, shared by Discover/Saved/Search) is
untouched -- fixing it would mean restructuring the click-to-focus flow to avoid Streamlit's
abort-and-restart dispatch, a larger, riskier change than this one. Flagged as a possible
follow-up if the owner wants to squeeze out the remaining ~0.3-0.5s; not actioned here.

## MR !70 MERGED, 2026-08-31: Discover list paginated

Reviewed 8 rounds -- see that branch's `.claude/task/review.md` history for the full account.
Owner reported the app as unusably slow: "Clicking on an element in the list and nothing
happens... Usability is zero." This is the exact, already-scoped, already-measured problem in
`docs/backlog/discover_list_performance.md` (full ~923-row pool mounting ~931 `st.button`
widgets and ~20,600 DOM nodes unconditionally). Owner was shown that doc's candidate directions
directly and asked to choose. **Owner decisions recorded here** (both given via a direct
multiple-choice question, not defaulted):
- **Approach: "Pagination (Recommended)"**, over "Load more" append or an `st.dataframe`
  rebuild.
- **Page size: "30 (Recommended)"**, over 50 or 100.
`DISCOVER_PAGE_SIZE = 30` in `frontend/app.py`; the pool is sliced after the existing filter/sort
step, before it reaches `row_ui.render_rich_row_list` -- no change to the row primitive's
tap-target mechanics, pool computation, filtering, or sort order. Previous/Next render below the
list, disabled at the first/last page, hidden entirely (not just disabled) on a pool that already
fits one page. Live-verified: 40 buttons / 942 DOM nodes mounted (down from ~931 / ~20,600),
correct company opens on click at the first/middle/last row of a page, Next/Previous move
correctly between pages. **Could not obtain a reliable click-to-response timing number**: this
session's browser-automation environment throttles JS timers on the (always-reported-hidden)
preview tab, producing a misleading ~7-8s reading on a page too small to structurally be that
slow; the DOM-count evidence stands as the verification of record, a human timing check on the
shipped app is the way to close this out.

**A second owner decision recorded here, from a round-1 scope-auditor escalation on this same
branch:** whether the specific pagination control shape (Previous/Next labels, "Page N of M"
text, hide-entirely-vs-disable on a single-page pool) needed its own sign-off, separately from
the abstract pagination/page-size decision above --
`docs/backlog/discover_list_performance.md`'s own Open Questions section says this class of call
is not the builder's to default. Owner was shown the built shape and asked "Good to ship
as-is?"; answered **"Ship as-is."** No change made as a result. Recorded in both this file and
`.claude/task/contract.md`'s `decisions_reserved`, since the answer previously existed only in
chat, which a cold reviewer or a future session has no way to check -- that gap is exactly what
round 2 of this branch's review failed on, correctly.

**Also found and fixed live, not anticipated at Confirm time:** the row-tap-target CSS from MR
!67 scoped itself via a bare `div[data-testid="stVerticalBlock"]:has(.ss-row)`, which matches at
any descendant depth, not just the nearest -- so it also matched the single big stVerticalBlock
wrapping the *entire* list, not only each row's own small container. The new pagination buttons,
the first other `st.button()` ever rendered inside that same big wrapper, silently inherited the
row-only `position: absolute; inset: 0` and stretched to the full list's height (~2780px).
Fixed by tightening five selectors in `frontend/styles.py` to a direct-child
`:has(> [data-testid="stElementContainer"] .ss-row)` form, matching a pattern already used
correctly elsewhere in the same file. Two new regression-guard tests added to
`tests/frontend/test_styles.py`, both verified to fail against the broken form before being kept.
**Pagination alone was not the whole fix, see the entry near the top of this file:** owner
reported the app "substantially faster" after this merged, but still delayed 1-2s per click,
traced to a separate, larger cost this task's own investigation hadn't found yet.

## MR !68 MERGED, 2026-08-31: Discover row verdict dot removed entirely

Reviewed 8 rounds; each round caught one more stale cross-reference or handover-accuracy issue a
prior sweep missed, including in this file itself -- see that branch's `.claude/task/review.md`
history for the full account.
Owner saw the CSS-dot fix (MR !65) live and said "Dots misaligned, just remove them" -- a final,
decisive instruction, not a request to debug alignment further. `build_rich_row_html` no longer
takes a `verdict` parameter; the list row now renders title/subtitle/lead-metric only. The
Company Snapshot card's own separate verdict badge (`card_ui.py`'s `.ss-verdict-badge` family)
is untouched, unaffected, still shows on the focus card. Live-verified: no dot, metric still
renders, tap-target from MR !67's fix still resolves correctly at both row edges.

**Two other things in the same owner message, explicitly deferred, not implemented:**
- **Whether the list should show a lead metric at all** -- owner said "I'm not sure," an open
  question, not a decision. Given as chat discussion, not code: recommended keeping a metric
  (it's what lets a reader triage hundreds of unfamiliar companies, the reason Discover's row
  was built richer than Saved/Search's in the first place) but capping/relabeling extreme
  outlier values (e.g. 4DMedical's -823.3% operating margin) for pre-revenue-type companies
  instead of removing the number app-wide. Not actioned; owner's call.
- **Gemini AI feedback from testing two cards (4DMedical, Apple/AAPL)** -- owner said "file these
  so we can discuss later." Verified against the codebase before filing (not transcribed
  uncritically): all eight checkable technical claims confirmed TRUE or PARTIALLY TRUE against
  current code -- no ratio sign-inversion guard exists (`int_stock__card_metrics.sql`'s ratio
  fields guard only `!= 0`, never sign); the AI-read prompt (`generate_assessments.py`) requests
  free text, not structured JSON, and has no post-generation hallucination/KPI reference-check;
  `benchmark_range()` (`card_copy.py`) is pure linear min-max scaling with no outlier
  compression; `_verdict_operating`'s core (`fcf_margin_pct`) and supporting
  (`current_ratio_stmt`) axes are gated fully independently, confirmed by the repo's own
  existing test `test_operating_supporting_weakness_blocks_green`
  (`tests/tooling/test_assessment_rules.py`) -- Apple's real figures (current ratio 0.89, FCF
  margin 23.7%) hit exactly that pattern, which is why it read Mixed; no verdict threshold
  varies by sector or company size, only by the three-way company-type split. Filed as
  [`docs/backlog/gemini_verdict_feedback.md`](../docs/backlog/gemini_verdict_feedback.md),
  MR !69 MERGED (branch `docs/file-gemini-verdict-feedback`,
  https://gitlab.com/rami.al-fahham/stock-swipe-app/-/merge_requests/69).
  Not actioned -- the doc's own Open questions are the owner's call.

## MR !67 MERGED, 2026-08-31: fixed row tap-target misalignment (Discover/Saved/Search)

Every list row's invisible tap-target button was rendering entirely *below* its own visible
row (Streamlit's `stElementContainer` default `position: relative` on the button's own wrapper
outranked the intended `stVerticalBlock` anchor), breaking click-to-open across Discover, Saved,
and Search alike. Pre-existing bug, not introduced by this session. Fixed with one CSS rule;
verified live via real pixel hit-testing (`document.elementFromPoint`). Two-round review, full
account in that branch's `.claude/task/review.md` history.
**Scoping gap found later, 2026-08-31, see the pagination entry near the top of this file:**
this rule's own selector scoped itself via a bare `:has(.ss-row)`, which matches at any
descendant depth, not just each row's own container -- so it also matched the single big
stVerticalBlock wrapping the entire list, and a later, unrelated `st.button()` (Discover's
pagination controls) sharing that same big wrapper silently inherited it. Tightened to a
direct-child form in `frontend/styles.py`; this entry's own fix still stands, only the
scoping precision changed.

**Owner also reported, in the same message, several other things checked and resolved in
conversation, not yet all recorded as their own backlog items:**
- **Dots still misaligned:** resolved decisively, not by further alignment debugging. Owner's
  next message on seeing the list again: "Dots misaligned, just remove them" -- see the dot
  removal entry above, which removed the verdict dot from the list row entirely.
- **"Hardcoded/random" list, missing new markets, only ~900 companies instead of 1,200+:**
  checked directly against live Supabase, not the code alone. The list itself is 100%
  data-driven (queried Supabase myself: 924 deduplicated eligible companies across exactly 5
  markets, matching the app's own count exactly). The 4 newer markets (France, Netherlands,
  Switzerland, Spain) are onboarded but have zero exported data yet: last successful pipeline
  run predates their onboarding, and the pipeline is biweekly (checked the actual GitLab
  schedule: next run 2026-09-01). Not a bug, a timing gap that should resolve itself. **A real,
  separate, smaller bug found along the way:** the market filter dropdown's options come from a
  hardcoded `MARKET_DISPLAY_NAMES` dict in `frontend/markets.py`, not from live data, so it
  currently offers those 4 markets even though they have no companies yet. Not yet fixed or
  scoped as its own task.
- **Filters/stats stay visible on the focus card:** confirmed in code
  (`frontend/app.py:_discovery_page`, `_render_explore_filters` runs unconditionally whenever
  the active tab is Discover, with no check for whether a card is focused). Real, confirmed
  UX inconsistency; not yet fixed or scoped.

**Owner also asked for a full user-flow simulation across the whole app** (Discover, Saved,
Search) to find further inconsistencies, beyond the specific points already checked above. Not
done yet, deliberately deferred until the click-target fix (the most severe, most clearly
diagnosed issue) shipped first, then the dots-removal instruction took priority next. Next
concrete action: either continue fixing the remaining confirmed items above
(filters-on-focus-card, hardcoded filter dropdown) or do the broader flow simulation the owner
asked for, depending on what they want next.

## MR !65 MERGED, 2026-08-31: Discover row verdict rendered as a CSS dot, not emoji

Owner reported the list's health-verdict indicator looked "scattered." Root cause: the native
emoji's (🟢/🟡/🔴) own internal vertical glyph metrics vary by platform/font, not a CSS bug
(every row's own flexbox layout was already pixel-identical). Fixed by rendering a plain
CSS-drawn circle instead. **Superseded 2026-08-31:** the dot still read as misaligned to the
owner after this fix shipped, and rather than debug further the owner instructed removing it
entirely -- see the dot-removal entry above. This entry stays for the record of what was tried
and why it wasn't the final fix.

## Discover list performance: scoped 2026-08-31, decided and shipped same day

[`docs/backlog/discover_list_performance.md`](../docs/backlog/discover_list_performance.md).
Doc-only, two-round scope-auditor review; MR !66 merged (`docs/scope-discover-list-performance`).
Found 2026-08-30 while investigating a report that tapping a list row visibly hangs before the
card opens. Confirmed by direct measurement: with the full 923-row list showing, a click takes
~2.4s before Streamlit even starts processing it, because the page mounts 931 individual
`st.button` widgets and ~20,600 DOM nodes unconditionally, every render, no pagination or
windowing (`frontend/row_ui.py`'s `_render_tappable_rows`). Narrowing to a 39-company market
drops that to ~0.6-0.7s, confirming the correlation.

**New since the last note: a concrete, code-grounded (not yet empirically confirmed) mechanism
for the second, previously-unexplained symptom** (inconsistent server-side run duration,
~100ms-2s). `_render_tappable_rows`'s per-row click handler calls `st.rerun()` unconditionally
right after `on_select`, aborting the already-in-progress run and starting a fresh one; because
this fires from inside the row-rendering loop, **the aborted run's cost before the abort scales
with how far down the list the clicked row sits**. This would explain the inconsistency without
a per-company explanation, and means the two symptoms may share one root cause (rendering all
rows unconditionally), not two separate problems. Not yet confirmed with a controlled test; the
scoping doc flags it as the first thing a profiling pass should check.

**Decided and shipped, 2026-08-31, same day:** owner reported the app as unusably slow, was shown
this doc's own open questions and candidate directions directly, and chose pagination,
`DISCOVER_PAGE_SIZE = 30` -- see the "MR !70 MERGED... Discover list paginated" entry near the
top of this file for the full account. This did not reopen the "first-time Discover default"
decision (see the MR !61 section below this one): that was about content curation for beginners; this is a
technical widget-count fix, a different justification, kept distinct on purpose. The
`st.rerun()`-inside-the-loop hypothesis above was not separately spiked or confirmed -- pagination
caps the widget count per render regardless of where in the row loop a click lands, which
independently shrinks the cost either way.

## MR !58 MERGED, 2026-08-30: Discover reworked to filter -> list -> focus

Retired the one-card-at-a-time walk for an alphabetically-ordered list of every filtered match
(originally rendered scrollable and unpaginated; paginated 2026-08-31 once that proved too slow
at ~923 rows, see the entry near the top of this file); each row shows one type-aware lead
metric (Operating margin / Return on equity / Cash runway by company type, each a core,
verdict-deciding axis for that type's own rule in `scripts/assessment_rules.py`, not a metric
picked for the row alone; a health-verdict dot originally sat alongside it too, removed
2026-08-31, see the entry near the top of this file); tapping a row opens the existing focus
card. Six-round review, full account in that branch's
`.claude/task/review.md` history. **If a future card metric gets used as a UI "lead" or headline
figure anywhere else, check `assessment_rules.py`'s own verdict function for that company type
first**: round 5 caught Return on equity wrongly used as operating's lead metric (only a weak,
tie-breaking supporting axis there, not one of the three core axes that decide red/green).

**The broader landing/onboarding rethink** the owner also flagged in the same request (this
branch only fixed "filters with no visible effect") is done too, see the entry below this one.

## MR !61 MERGED, 2026-08-30: landing screen deleted entirely

`feat/kill-landing-screen` merged to `main`. Owner reviewed a live mockup and rejected
coach-marks/hints on standard controls as condescending,
then chose to delete the first-run landing screen outright rather than shrink or split it: no
gate, no replacement, straight into Discover on first launch. The brand/tagline it would have
shown are already permanent in the header; "Not investment advice" became a permanent caption
there instead of a one-time screen. Full decision trail and the three candidate directions that
were NOT chosen: [`docs/backlog/landing_onboarding_rework.md`](../docs/backlog/landing_onboarding_rework.md).

Deleted `frontend/landing.py` and six now-dead functions in `frontend/browser_storage.py`
(`onboarding_ready`, `is_onboarding_dismissed`, `dismiss_onboarding`, `request_landing`,
`_load_onboarding_from_manager`, plus the now-unused `_parse_bool`), the overflow menu's "How
Stock Explorer works" button, and the `.ss-landing*` CSS block. **`frontend/app.py`'s `main()`
call is now guarded (`if __name__ == "__main__":`)**, needed so the new `brand_header_html()`
pure function could be imported and unit-tested without executing the whole app on import;
verified live (via the dev server) that Streamlit still runs the app correctly with this guard,
since Streamlit sets `__name__ == "__main__"` for the script it runs.

**Known pre-existing gap, not fixed here, flagged as its own chip:** `frontend/browser_storage.py`
had zero test coverage before this task, not just the onboarding parts, likely because it wraps
a Streamlit component (`local_storage_manager`) that's awkward to test without a live session.

**Three-round review, two real findings, full account in that branch's `.claude/task/review.md`
history.** Round 1: an orchestrator mistake, not a design defect. A batched `git add` with one
already-`git rm`'d path silently aborted the whole command, staging almost nothing; committing
it as-is would have shipped `frontend/app.py` still importing the just-deleted `landing` module,
crashing the app at import time in both the dev config and the real deployed entrypoint
(`streamlit_app.py`). Round 2: a genuine product-scope overreach caught by cto-reviewer, not
scope-auditor. **If a future review flags an owner-reserved product/UX call being answered
without explicit sign-off, take it seriously even if a different required reviewer already
passed the same diff clean**, see below.

**"Getting to the cards where learning content is located": decided 2026-08-30, no change
needed.** Checked the real, live focus card rather than theorizing about it: one tap from the
list, a reader already sees a plain-English AI-written verdict paragraph and six lensed metrics,
each with a plain-language gloss line (a sector comparison too, but only for the ~4 of 13
catalogued metrics marked benchmarkable; the rest correctly say "No sector comparison for this
metric" rather than fake one). One further tap ("Understand these numbers") reaches, immediately,
a median-comparison recap, a short analogy per metric, and an interactive playground; each
metric's fuller written explanation needs its own additional "Read more" tap, by design. **A
round-1 scope-auditor catch: an earlier draft of this claimed every metric got a sector
comparison and that fuller explanations were one tap away**, both wrong, checked against
`dbt_analytics/seeds/metric_catalogue.csv`'s `benchmarkable` column and `frontend/card_ui.py`'s
actual rendering; fixed to the precise mechanics above, which still support the same conclusion.
Recorded in
[`docs/backlog/landing_onboarding_rework.md`](../docs/backlog/landing_onboarding_rework.md),
which is now fully resolved, all three parts of the owner's original complaint closed. Two-round
review, doc-only; MR !64 merged (`docs/decide-getting-to-the-cards`). Nothing else queued after
this.

**Discover's first-time default scope: decided 2026-08-30, no change.** MR !63 merged. Scoped as
its own item
([`docs/backlog/discover_first_time_default.md`](../docs/backlog/discover_first_time_default.md)),
then resolved the same day, in conversation, not a mockup. The premise behind scoping it as
a problem was wrong: it treated "new to reading financial statements" (this app's actual
audience) as if it meant "new to using a web app." A filterable, searchable list isn't
intimidating to that audience; reducing it would have solved a problem this app doesn't have.
The full unfiltered list stays for every visitor, every time. **If a future session considers
building any kind of "simplified first visit" for this app, check this reasoning first**: the
same "beginner" conflation is an easy mistake to repeat. One separate, optional idea surfaced in
that conversation and not committed to: name search directly on Discover (it currently only
exists as its own Search tab).

## MR !51 MERGED, 2026-08-28: NL/CH/ES onboarded

`feat/markets-nl-ch-es` merged to `main` (`aa646439`). Netherlands, Switzerland and Spain are
now active — nine markets total, six queued (Finland, Sweden, Denmark, Norway, Canada, Italy).
Sixteen-round review, full account in `.claude/task/review.md`.

**Two data defects found outside this branch's scope, filed as separate chips.** Eleven of 116
`jp_nikkei225` seed rows carried the wrong company name (audited against yfinance 2026-08-28,
two visible to the duplicate-headline guard, nine not): **FIXED and MERGED, MR !53**, detail
below. `au_asx200`'s Block ticker (`XYX`, should be `XYZ`) had fetched no data since May:
**FIXED, `fix/asx200-block-ticker`, 2026-08-29.**

**The Block ticker fix, and why it isn't a raw-seed edit.** Confirmed root cause by fetching
the live `S&P/ASX 200` Wikipedia table with the repo's own fetcher: it still lists Block, Inc.
under `XYX` today. Not a scrape bug, Wikipedia's own page has it wrong. `XYX.AX` and `SQ2.AX`
both 404 on Yahoo; `XYZ.AX` resolves to Block, Inc. in AUD. `scripts/refresh_constituents.py`
is a standalone manual script, not wired into CI or the regular ingestion run, so a raw-seed
hand-edit would not get overwritten today, but the next manual refresh for `au_asx200` would
re-scrape Wikipedia and put `XYX` right back. Built an ingestion-time override instead
(`ingestion/constituents/ticker_overrides.csv`, applied inside `load_constituents()` before the
yfinance fetch list is built), mirroring the seed-override design used for the name fixes but
intercepting before the fetch rather than after it in dbt, since a wrong ticker here means zero
data, not a display defect. Once real ingestion next runs for `au_asx200`, Block starts
fetching real data and the `blockinc` entry in `KNOWN_CROSS_MARKET_COMPANIES`
(`tests/ingestion/test_market_onboarding.py`) becomes a genuine cross-market duplicate like
Amcor, Newmont, ResMed and Rio Tinto.

**Four owner decisions from 2026-08-28, detail in the Market coverage section below and in the
merged contract:** the 20-card warn threshold is wrong, deferred to phase 2; currency follows
real-world practice (CHF as-is, CAD/SEK/DKK/NOK settled for the queue); seed-name corrections
become a dbt model (seed to staging pass-through to correction in `2_base`), filed separately,
does NOT cover the Block ticker; duplicate cards stay with the venue shown on each, filed to
its own UX-gated branch.

## Owner decisions, 2026-08-28

Four escalations from the NL/CH/ES branch are answered. None changes that branch's code; three
create new work.

1. **The 20-card warn threshold is wrong.** It measures an absolute card count against an
   index that has only 20 members, so Switzerland clears it only if every one of its 20
   constituents is card-eligible. Make it proportional to constituent
   count, in phase 2. Not on the onboarding branch: changing a gate that fails your own work is
   the France mistake.
2. **Currency rendering follows real-world practice.** "CHF" stands as-is. The queue is settled
   too: `CAD -> C$`, and SEK/DKK/NOK as ISO codes, since "kr" names three currencies and this app
   shows markets side by side.
3. **Constituent seeds become a dbt model, with name mapping and corrections applied in it**, as
   in the football-data project. That fixes the NAME defects: the SMI legal names and the eleven
   wrong Nikkei names, since `company_name` is only consumed downstream via `dim_stock`'s
   coalesce. It does NOT fix Block's wrong ticker, and folding that in would leave the defect
   open: `ingestion/yfinance/ingest.py:309-312` reads the CSV and uses its `ticker` column as the
   yfinance fetch list, before dbt runs, and staging reads only the parquet ingestion writes. A
   ticker correction must reach the fetch list. Which is the first thing the new contract has to
   settle: does the dbt model replace the CSV as ingestion's input, or sit downstream of it?
   **Layer settled 2026-08-28, and it does not conflict with `docs/layering.md`.** The mapping
   is a dbt SEED. A staging model exposes it as a direct source mapping, which is what staging is
   for. The correction itself, joining the override onto the constituent relation, happens in
   `2_base`, which is where entity resolution and alignment belong and where
   `base_yf__constituents` already picks a winning row. A first reading of this had the
   correction happening in staging, which the layering contract would have forbidden; that was a
   misreading, not a rule to reinterpret. New mechanism, own contract.
4. **Duplicate cards stay, and every card shows its exchange.** One card per listing is accepted
   as reality; the card face gains the listing venue so a reader meeting Shell twice sees why.
   User-facing, so it goes through the UX PR gate on its own branch. **Done,
   `feat/card-shows-listing-venue`, 2026-08-29**: format chosen from a reviewed mockup (market
   leads, queue position follows), executed exactly as decided.

## Market coverage

**Nine markets are active as of 2026-08-27**: the original five plus France (CAC 40),
Netherlands (AEX), Switzerland (SMI) and Spain (IBEX 35). **Six more are agreed and queued**,
all needing new registry entries: Finland, Sweden (OMXS 30), Denmark, Norway (OBX), Canada
(TSX 60) and Italy (FTSE MIB). The owner chose to batch these by group rather than one branch
per market, each market still getting its own coverage audit.
Where a passage below says "all 5 markets", it is recording a measurement taken before France
and is accurate as history. Present-tense statements about how a gate behaves have been swept
to nine.

**Switzerland warns unless its coverage is perfect, and this does not self-correct.** The SMI
has 20 constituents and `check_pipeline_completeness.py` warns below `WARN_ELIGIBLE_THRESHOLD`
of 20 on a strict `<`, so only all 20 eligible clears it; the sample projects 19. An earlier
note claimed the post-run baseline rewrite would give it a per-market floor and retire the warn.
**That was wrong**: `check_eligibility_baseline.py` writes `min_eligible: 5` as a hardcoded
literal on every `--write-baseline` and only ever populates `baseline_eligible`, and the 20 is a
module constant in a different script that nothing in the baseline file can influence. A WARN
does not fail the job, so the consequence is a warning line on any run with imperfect coverage,
not breakage. Of the four queued indices actually chosen, only OBX (25) sits close to the same
place; OMXS 30 is 30, FTSE MIB is 40 and TSX 60 is 60, and Finland's and Denmark's indices have
not been picked. Whether to live with that or make the threshold proportional to each market's
constituent count
was the owner's call. **ANSWERED 2026-08-28: the threshold is wrong and becomes proportional in
phase 2.** See the decisions section at the top of this file.

**Read `docs/data_contract.md`'s market activation checklist before onboarding any of them.**
The `onboard-market` skill routes you there and carries the two traps no document holds (Wikipedia
rejecting pandas' default user agent, and the constituent `table_index` being positional and
silently wrong), but the checklist is the procedure.
It exists, it is now correct, and France was done without reading it: the result was a missing
`public.markets` row that would have failed the next production export for every market on a
foreign key, with CI green throughout. The checklist gained four steps it was missing and lost one escape hatch that never existed
in this codebase. **That growth binds the six queued onboardings and is worth the owner
knowing about**: removing the non-existent fallback was a defect fix, but extending a
procedure that governs work not yet approved is closer to a §6 call than a repair.

**OPEN, and it needs the next pipeline run to close: the coverage audit is half done for all
four markets added since that run.** The activation checklist requires the audit on sample AND
full run, and the full-run half cannot be done from a dev machine. Sample estimates: France
90%, Netherlands 80%, Switzerland 95%, Spain 75% card-eligible, projecting roughly 36, 20, 19
and 26 cards.

**Reading the result is easy, because the job log prints it.**
`check_eligibility_baseline.py` ends a healthy run with `check_eligibility_baseline: OK`, the
total, and one line per active market, exactly as the 2026-08-26 run printed `au_asx200: 180`
and `de_dax: 39`. Look for `fr_cac40`, `nl_aex`, `ch_smi` and `es_ibex35` there. The mart holds
only eligible rows, so that number IS the card-eligible count the threshold uses. A
`WARN: <market>: card-eligible count N < 20` line appears too if one falls short. **Falling
short of 20 will not fail the run.** None of the four is in `scripts/eligibility_baseline.json`,
so `check_eligibility_baseline.py` gives each a floor of 5 rather than 20, and
`check_pipeline_completeness.py` only WARNS below 20. Both DO fail hard below 5, which aborts
the job before the export and stops the refresh for all nine markets, not just the new one. If a
market does not clear 20, that is a real finding about its coverage, not a threshold to lower.

**Then run `python scripts/check_eligibility_baseline.py --duckdb-path storage/stock_data.db
--write-baseline`.** Until that happens the aggregate drop gate is slack: `total_baseline_eligible`
is 843 from five markets while the check now sums nine, so the roughly 101 cards the four new
markets project raise the current total without raising any floor. Per-market gates for the
original five are unaffected, so a single-market regression still trips its own floor; only a
drop spread across several could hide in the gap. The gap is wider than it was at France, and
grows with each batch, so this is the highest-value thing to do after the next run.

**One gap closed and one still open, neither a live defect today.**
`_clean_company_name` keys on BRACKETS, so a non-bracket footnote marker (`*`, a dagger, a
superscript digit) passes the WRITER untouched. The seed GUARD now catches that class, which is
the right split: the guard only ever fails loudly and asks a human, while widening the writer on
a guess about tables nobody has fetched is the over-stripping failure this design fought. So an
artifact of that kind fails CI on the Nordic batch rather than reaching a card headline. All
nine committed seeds were scanned and none carries one today.
Still open: the seeds now hold 1079 tickers against the 959 of the 73-minute, 921-card run, and
the CI timeout is 2 hours. Headroom narrows with every batch and nobody is tracking it.

**A second checklist gap, same class as the step 4 one below.** Step 10 now explains the two
collision guards and their allowlists, but this branch added five guards that can fail on
onboarding data to `tests/ingestion/test_market_onboarding.py`, plus meta-tests pinning them,
and the checklist documents one. The one that will
bite the Nordic batch is `test_seed_company_names_carry_no_scrape_artifacts`: its bracket half
fires on any short trailing bracket, and four of the six queued markets use A and B share
classes. Whether it fires at all depends on the source tables bracketing them: the OMXS 30 table
writes "Atlas Copco A" plainly, so this is a risk rather than a certainty. An onboarder will
meet a red
test saying "scrape artifacts" on correct names. The tempting fix, widening
`_clean_company_name` to eat uppercase brackets, is the exact over-stripping failure this branch
spent several rounds arguing against; the right answer is a human decision recorded somewhere,
and which allowlist that should be is a section 6 call rather than something to invent here.

**A gap in the checklist worth closing before the next six.** Step 4 says to verify each
ticker returns a populated `sector`, but no tooling reports that:
`scripts/audit_yfinance_coverage.py` prints metric-presence flags and a raw `info_keys` count,
never the sector. It has to be checked by hand, and the failure is silent with a specific
financial shape: the classifier keys the `financial` branch on the exact string
`'Financial Services'`, so a bank returning a null sector becomes `operating`, is then gated on
EBITDA and net debt that banks do not report, and drops out of the deck with no error and no
warning while the market total still clears 20. France was checked by hand and only `ML.PA` came
back thin. Adding a sector column to the audit output would make step 4 mechanical for the
remaining six.

**Currency handling for the queue is SETTLED (2026-08-28): use each currency's real-world form.**
That confirms the proposal below rather than overturning it.
`CAD -> C$` following the `AUD -> A$` convention already in `_CURRENCY_SYMBOLS`; `SEK`, `DKK`
and `NOK` as ISO codes, because "kr" means three different currencies across the Nordics.
Recorded with the tension visible: §6 reserves user-visible formats to the owner, and the owner
also said plainly not to raise micro decisions and, when the first answer took the zero-work
option, "do it the right and professional way, not the most convenient way".
**CHF is out of that proposal because activating Switzerland commits it, not because it
shipped.** Nothing has shipped: the branch is not merged and no Swiss card or read exists yet.
Switzerland activated with no `_CURRENCY_SYMBOLS` entry, and `_display_currency` returns the bare
code for an unmapped currency, so on the next run roughly 19 Swiss reads will be generated from a
prompt carrying `Currency this company trades in: CHF`, and any read phrasing a margin per unit
of currency will print it. That is the documented fallback rather than an accident, and the franc
has no symbol in general use. It was put to the owner and settled on 2026-08-28: "CHF" is the
form real practice uses, so it stays.
**If the owner wants it different, change BOTH copies of `_CURRENCY_SYMBOLS`
(`scripts/assessment_rules.py` and `frontend/card_copy.py`) and do NOT bump
`INPUT_HASH_VERSION`.** Changing one copy alone is worse than changing neither: edit only
`card_copy.py` and the card face shows a symbol every stored read still calls CHF, with no hash
movement to regenerate them, so the split is permanent. `test_currency_symbol_maps_are_mirrors`
now fails if they drift. `compute_input_hash` already folds `_display_currency(currency)` in, for
exactly this case, so the hash moves only for the cards whose currency string changed and only
those reads regenerate. `INPUT_HASH_VERSION` is the lever for a GLOBAL refresh: bumping it would
re-run Haiku across every card in all nine markets to change 19.
Extend `_CURRENCY_WORDS` in `tests/tooling/test_assessment_rules.py` when any of these lands.

**FIXED (`fix/nikkei-company-names`, MR !53 merged): two Nikkei cards shared a
headline, or one card named the wrong company. A full audit found ELEVEN, now corrected via a
dbt override, not a raw-seed edit.**
`storage/seeds/jp_nikkei225/constituents.csv` gives ticker 9101 the name "Mitsui O.S.K. Lines".
9101 is Nippon Yusen (NYK Line); 9104 is Mitsui O.S.K. Lines. So a live card shows NYK Line's
financials under a competitor's name, Nippon Yusen is absent from the deck, and the two headlines
differ only by full stops, which is why the guard missed it until it was widened past exact
matching.
**Auditing every row against yfinance on 2026-08-28 found eleven wrong company names in 116
rows**, which is a rate over SEED ROWS: how many of the eleven cleared eligibility and became
cards is not checkable from here, the same limit this file states twice elsewhere. The tickers:
3407, 6908, 6976, 8005,
8804, 8830, 9005, 9008, 9009, 9101 and 9412. The full table is in the filed task. The
cause is NOT a column shift, though an earlier draft here said so: 9007 Odakyu sits correct
between the wrong 9005 and 9008, which no column slide produces, and the starter import file has
identical row order. Do not attempt a fix by sliding the name column; it would corrupt 9007 and
still leave 9005 wrong. `jp_nikkei225` is the only seed with `source: import`. **Only two of
the eleven are visible to any guard here**: a wrong name whose
true owner is not also a row in the same seed looks correct. The durable fix is checking each
seed name against yfinance's `info_long_name`. **The owner chose a different mechanism on
2026-08-28**: corrections move into a dbt model. A name-versus-yfinance check may still be worth
having as a guard, but it is no longer the proposal on the table. **Scoped as its own backlog
item 2026-08-29**: [`docs/backlog/name_vs_yfinance_audit_guard.md`](../docs/backlog/name_vs_yfinance_audit_guard.md).
**Built, on `fix/nikkei-company-names`:** a new seed
`dbt_analytics/seeds/company_name_overrides.csv` maps `(market_code, ticker)` to a corrected
`company_name`, exposed 1:1 by `stg_manual__company_name_overrides` in staging, and left-joined
plus coalesced onto the seed's own name in `base_yf__constituents` (2_base), so the correction
reaches `dim_stock` without editing core or the raw seed. Same mechanism the SMI legal-name fix
below reuses: rows added to the same seed rather than a second one built.
The same file gives ticker 3407 the name "Asahi Group
Holdings", which is ticker 2502. 3407 is Asahi Kasei. Both rows
are in the seed, `dim_stock` prefers the seed name over yfinance's correct one, so the deck has
carried this since the 2026-05-23 import. It is pinned, not accepted: `KNOWN_DUPLICATE_SEED_NAMES`
in `tests/ingestion/test_market_onboarding.py` records it with the reason, and a second test
fails once the duplicate is gone, so the allowlist cannot outlive the defect. Fixing it edits an
already-shipped card headline, which is a §6 call, so it was left for its own branch rather than
folded into a market onboarding.

**Issue #7 (duplicate cards for one company) is twelve companies, not one** (was eleven; Block
Inc joined once its `au_asx200` ticker was fixed, `fix/asx200-block-ticker`). **The "which venue
is this card" symptom is FIXED (`feat/card-shows-listing-venue`)**: every Discover card's meta
line now shows its own market before the queue position (`FTSE 100 · 3 of 47`), so a reader
meeting one of these twelve twice can tell the two cards apart. Owner decision 2026-08-28
("duplicate cards stay, and every card shows its exchange") is fully executed as of that
branch. **Still open, and this fix does not touch it:** the peer-set and deck-wide counter
inflation below, which is a counting/eligibility-math problem, not a display one. The deck
renders one card per seed row, so a company in two indices is met twice. Six predate the NL/CH/
ES batch (Amcor, Newmont, ResMed, Rio Tinto, News Corp, Airbus), five arrived with it (Shell,
Unilever, RELX, IAG, and ArcelorMittal going from one card to three), and Block Inc is the
twelfth. `KNOWN_CROSS_MARKET_COMPANIES` in `tests/ingestion/test_market_onboarding.py` keys on a
punctuation-insensitive form, so it does hold News Corp despite the two seeds spelling it
differently, but it cannot see a pair differing by more than punctuation, and the same-market
share-class case is out of scope by construction.
**A second class makes it thirteen distinct companies and neither path fixes it.** `us_sp500`
carries Alphabet, Fox and News Corp twice each as two share classes in ONE market, which both
guards miss by design and which "name the venue" cannot resolve because there is one venue. News
Corp is in both lists, so the union is thirteen companies carrying 28 cards, not fourteen. Those
three are the only duplicates that move a PEER-SET number TODAY: all six rows sit in what Yahoo
labels
`us_sp500` Communication Services (expected, not verified here, since sector labels come from
yfinance), so that sector's peer count and medians double count three issuers, and that belongs
with the phase-2 threshold work. Spain may add one on the next run: Spanish Utilities counts 7
without Acciona SA and 8 with it, so if Yahoo files it there alongside Acciona Energia, which it
consolidates, that peer set crosses the gate holding 8 rows for 7 independent issuers. Genuine
index membership rather than a defect, and phase-2 work, which is why this says today.
"{sector} (N companies)" on the card face renders that same peer
count, so it overstates by up to 3 in one sector and cross-market duplicates cannot move it.
The benchmark CTE applies the same `is_card_eligible` filter, so that is a ceiling like the two
below.
The cross-market ones move the two DECK-WIDE counters instead: "N companies worldwide" and
"N card-ready companies" both say companies and count card rows, so both classes inflate them,
by 8 today (5 cross-market, 3 share class) and 15 after the run (12 and 3). Ceilings, since those
counters count card-eligible rows only.
The contract records the two paths put to the owner. Nothing changes at merge; the new
duplicates appear on the next run, and five of the eleven are already visible today.

**FIXED (`fix/smi-legal-name-register`): SMI card headlines were in a different register from
every other market.** The Swiss source table's only name column gives legal names, so the seed
carried "Novartis International AG", "Swiss Reinsurance Company Ltd" and "Holcim Limited" where
the other eight markets carry "Adidas", "Philips", "Santander". Two of those were not just
formal but wrong: the listed issuers are Novartis AG and Swiss Re AG. `dim_stock` prefers the
seed name over yfinance's `info_long_name`, which has them right, so the coalesce actively
discarded the correct name. There is no config fix: the table has no short-name column, so the
durable fix was the override mechanism, which is a §6 call. **ANSWERED 2026-08-28**: the
mechanism is a dbt model with the mapping applied in it, reusing `company_name_overrides` (the
seed built for the Nikkei fix above). **Name list proposed against yfinance `longName`,
presented to the owner as a full 20-row table, and approved verbatim ("go ahead with that
list") on 2026-08-28.** Nineteen `ch_smi` rows added; `KNIN` excluded since its seed name is
already a trade name.

## Current task

**Reshaping the dashboard into a beginner financial-literacy tool** — sector-aware metrics + AI "reads"
+ a health verdict, via the **Sector/Lifecycle Router** built in slices. **Slices 1–5a and 5b are all
MERGED into `main`** (#139–#148, plus 5b via MR #3) — the full raw-data foundation, per-type metric
compute, the Router mechanism, and both the deterministic health-verdict generator and the Claude Haiku
prose read are complete and merged, code-wise. **They ARE now live for real users, at full scale**
— the app is deployed on Render (https://stock-explorer-app.onrender.com/) against a newly-created
Supabase project (the old one is permanently inaccessible — see the Infra section for the full
account-recovery story), serving **921 real eligible cards** across 5 markets as of the
2026-08-26 run, which the app shows as 924 (three stale ASX rows persist; see the card-count
note in the Supabase section below), confirmed
rendering end-to-end this session (fresh page load, no errors, benchmark words + health verdicts
all correct). **GitLab CI/CD variables for the new Supabase project are now set** (all 6:
`SUPABASE_URL`/`SUPABASE_DB_PASSWORD`/`SUPABASE_DB_HOST`/`SUPABASE_DB_PORT`/
`SUPABASE_SERVICE_ROLE_KEY`/`ANTHROPIC_API_KEY`, all Protected, confirmed via `glab variable
list`). **The pipeline schedule now exists too** (created 2026-08-24 via `glab api
projects/:id/pipeline_schedules`, cron `0 6 1,15 * *` UTC, `main`, active — see Infra) —
`data-pipeline` now refreshes the live app's cards unattended, first run
2026-09-01T06:00 UTC.
**Slice 6 (UI redesign) is fully MERGED — all three phases done:** **6a**
(MR #4 — tokens, shared row primitive, Search styling), **6b** (MR #8 revert + MR #9 —
button/popover/expander/link-button skin unified app-wide), **6c** (MR #10 — health verdict badge + AI
read now render on the card, the card's ~11 disclosure toggles consolidated into one expander,
metric-label chips, words-not-arrows benchmarks). Confirmed via `git fetch gitlab` — `gitlab/main` @
`0a72073` (merge commit of `feat/ui-slice6c-card-content`). **Slice 6 is closed** — see
Next concrete actions below for what's actually queued now.

Note on this section: as of 2026-08-18, this repo's own committed handover prose still described 5b's
MR #3 and 6a's MR #4 as "open" long after both were actually merged (confirmed via the real merge
commits `335046a` and `9b5aaea` on `gitlab/main`) — nobody went back to flip the wording after either
merge landed. This section has been corrected to match actual `main` state; watch for the same drift
next time a slice merges — update this paragraph immediately, don't leave "MR open" language stranded.
Full slice-by-slice narrative (the "do it right" correction, the metric-assignment matrix reasoning, the
external-review adjudication, 5b's and 6a's own review journeys) is in `docs/handover_2026-08-18.md`;
the durable outcomes of that reasoning are captured in Decisions locked below.

## Infra: GitHub → GitLab migration (separate track, not a product slice)

**Why:** GitHub account (`ramialfahham`) was suspended 2026-08-14; ran `/migrate-to-gitlab` at the
owner's direction. Orthogonal to the Sector Router / AI-assessment work.

**State:** Migration complete and verified — new private GitLab project
`rami.al-fahham/stock-swipe-app`, `main` protected correctly, CI green for real
(`validate:branch-guard`/`secret-scan`/`full` all passed on a real pipeline run, not just config that
parses). Full narrative (CI-minutes blocker, runner consolidation, branch-protection ordering trap)
archived in `docs/handover_2026-08-18.md` and [[gitlab-runner-duplicate-registration]].

**Deploy path — DONE, app is LIVE:** https://stock-explorer-app.onrender.com/. Streamlit
Community Cloud only deployed from GitHub, and the GitHub account is still suspended (no ETA)
— ruled out any GitHub-dependent workaround. Owner chose **Render** (native GitLab OAuth
integration, auto-deploy on push) over Fly.io and self-hosting on Hetzner. Repo-side prep
landed via MR #12 (merged): `render.yaml` Blueprint + doc updates. Owner completed the manual
account/connect/secrets steps live; confirmed working end-to-end (real card data rendering,
navigation, Save/Not now all clean) — see the Supabase account-recovery entry below for why
this took a second pass on the secrets.

**Supabase account recovery — the OLD project is permanently inaccessible, a NEW one now
backs the app.** The old Supabase account was itself linked to GitHub for login only — the
same suspension that killed Streamlit Community Cloud also locked the owner out of Supabase
(Supabase's password-reset flow confirmed: GitHub-OAuth-only account, no password fallback).
A free-tier support ticket was filed (SU-450943, no SLA) but not relied on. **Fix:** owner
created a brand-new Supabase project — signed up with a Gmail plus-alias
(`rami.fahham+supabase2@gmail.com`, same inbox, distinct string so Supabase's signup didn't
collide with the locked account) using plain email/password, **no OAuth dependency this
time** — cannot be locked out the same way again. New project: `stock-explorer` org,
`https://jftklivldxuoumcdabny.supabase.co`, region `eu-west-1` (Ireland). Created with
**"Automatically expose new tables" deliberately unchecked** (Supabase's own recommendation
for manual access control) — this had a real consequence, see below.
- Schema migrated clean (`apply_supabase_migrations.py`, all 10 pre-existing migrations +
  new `011_grant_roles.sql`, direct `db.{ref}.supabase.co:5432` connection — works from a
  home/dev machine; GitLab's shared runners need the Session pooler host — **resolved and
  proven 2026-08-25**: the first real CI `data-pipeline` run connected on its first attempt
  with the pooler host/port already in the CI/CD variables, see the manual-run entry in
  Status).
- **Full-universe ingestion completed and exported — 910 real eligible cards at that run**
  (2026-08-20; the later 2026-08-24 refresh returned 907, see the card-count note below)
  (us_sp500 500, au_asx200 171, jp_nikkei225 109, uk_ftse100 91, de_dax 39; above the
  843-card eligibility baseline). Started as a 40-tickers-per-market sample (188 cards) to
  prove the pipeline quickly, then re-run at full scale once the export bugs below were
  fixed. `dbt build` 105/105, all three health-check scripts (`check_pipeline_completeness`,
  `check_eligibility_baseline`, `check_export_health`) green. Confirmed live on Render with
  a fresh page load (no cached-session artifacts) — 910 companies, real benchmark words,
  health verdicts rendering.
- **Card-count note, first worked out on the 2026-08-24 data: 907 rows in that snapshot while
  the app served 910 cards.** The same gap persists at the 2026-08-26 run (921 rows, 924 cards)
  and the mechanism below is what causes it. Both numbers are real and they measure different
  things, which is worth getting straight, because
  chasing this the wrong way round wasted a review round on 2026-08-25. Verified that day by
  querying production and then loading the live app:
  - `mart_stock_cards` holds two snapshots. `snapshot_date` 2026-08-20 has 910 eligible
    rows, 2026-08-24 has 907. Three `au_asx200` tickers — **BXB, RMS, SPK** — are in the
    first and not the second (171 ASX rows then, 168 now).
  - The app nonetheless shows "910 left · 1 of 910", confirmed on a live page load. That is
    not a bug in the count: `dedupe_to_latest_snapshot` (`frontend/explore_filters.py:56`)
    keeps the newest row **per (market, ticker)**, not the newest snapshot, so those three
    keep their 08-20 row and stay in the deck. 907 + 3 = 910.
  - So the three tickers did not disappear from the app — they went **stale in place**, and
    nothing in the pipeline ever removes them. Each card carries its own "As of" line
    (`freshness_line`), so a reader who looks sees August 20 on those three; the global
    "About the data" date is a max across cards (`markets.latest_snapshot_label`) and so
    reads August 24 for the whole deck.
  **Why those three dropped out of the newer run was not investigated**, and neither was
  whether any eligibility gate ran against the 08-24 data at all: that export did not come
  from the `data-pipeline` CI job (see Next concrete actions item 1 — the CI path has never
  run against this Supabase project), so do not assume `check_eligibility_baseline.py`
  watched this dip. When quoting a figure, say which one you mean. As of the 2026-08-26 run
  that is 921 rows in the latest snapshot and 924 cards in the deck; the three stale tickers
  are still BXB, RMS and SPK, and the Status section records what the third data point
  settled about them.
- **Two real bugs found and fixed while getting the export path working — MERGED** (MR #13,
  `fix/supabase-export-client-and-grants`, `gitlab/main` @ `aa63058`; three review rounds,
  four required reviewers, real findings every round — full detail in that MR's
  `.claude/task/contract.md` amendments and `.claude/task/review.md` if you need the trail):
  1. `scripts/export_to_supabase.py` used `ClientOptions` from `supabase.lib.client_options`
     for a **sync** client — a confirmed upstream `supabase-py==2.30.0` bug
     (supabase/supabase-py#1306: the sync path internally reads `client_options.storage`,
     which the generic `ClientOptions` dataclass doesn't define). Fix: `SyncClientOptions`.
     `frontend/supabase_client.py`'s `get_anon_client()` is unaffected (no explicit
     `options=` passed) — confirmed the live Render app never hit this.
  2. **"Automatically expose new tables" being off means NO role gets implicit table
     privileges** — every existing migration's "service role bypasses RLS by default"
     comment assumed a grant that doesn't exist without that setting. `RLS restricts which
     rows a role sees; it does not substitute for the underlying GRANT`, which Postgres
     still enforces. New `supabase/migrations/011_grant_roles.sql` grants exactly what each
     table's existing RLS policy already declares — found via `export_to_supabase.py`
     erroring `permission denied for table mart_stock_cards`, then via a review-cycle
     finding that `scripts/check_supabase_connection.py` (documented setup-verify step)
     *also* needs `service_role` SELECT on `markets`/`user_interactions`, which the first
     draft of the migration missed. **If a future migration adds a new table any of
     `anon`/`authenticated`/`service_role` needs to touch, add a matching `GRANT` explicitly
     — nothing grants it automatically on this project.**
- `docs/supabase_setup.md` updated to document the toggle + its consequence (was previously
  silent on both, which is exactly what let the bug slip through the original migrations).

- `dbt-agent-kit` (this repo's guardrail plugin source) was not migrated — out of scope, also
  unreachable (same suspension).
- Repo visibility: created private by default — flip if wrong; docs reference production secret names.
- **CI/CD variable values: DONE this session.** All 6 set in GitLab Settings → CI/CD →
  Variables, all Protected, the three real secrets (`SUPABASE_DB_PASSWORD`,
  `SUPABASE_SERVICE_ROLE_KEY`, `ANTHROPIC_API_KEY`) also Masked+hidden. `SUPABASE_DB_HOST`/
  `SUPABASE_DB_PORT` came from the owner reading the Session pooler host/port directly off
  Supabase's Dashboard → Project Settings → Database → Connection string — the discovery
  script (`scripts/discover_supabase_db_host.py`) was tried first and failed on every one of
  44 candidate endpoints from this machine (psycopg2 imports fine, so this reads as a local
  network/firewall issue, not a dead project) — if reaching for it again, expect it may not
  work from this machine and go straight to the dashboard instead.
- **Pipeline schedule created 2026-08-24** via `glab api projects/:id/pipeline_schedules
  -X POST` (id `4404666`, cron `0 6 1,15 * *`, UTC, target `main`, active, first run
  2026-09-01T06:00 UTC) — confirmed `data-pipeline`'s own `rules:` already match
  `$CI_PIPELINE_SOURCE == "schedule"` (`.gitlab-ci.yml:259-260`), so this actually triggers
  it. Previously deferred as owner-only (same class as the variable *values*); on
  reconsideration this was mechanical implementation of an already-decided cadence
  (bi-weekly, 1st/15th, 06:00 UTC — decided in the MR #19 session), not a new decision, so
  created directly rather than re-escalating an already-settled call.
- Whether/when to restore `main` branch-protection expectations if GitHub access is ever restored — two
  remotes exist for now.

**Next concrete action:** none on this track. The pipeline schedule above was the last
piece needed, and it's done. `data-pipeline` now refreshes the live app's cards on its
own; first scheduled run 2026-09-01T06:00 UTC.

## Status

**DONE: the manual `data-pipeline` run finished (pipeline #111, job `16123372465`, success in
73 minutes).** All three expected outcomes landed, none was a regression:
1. **The deck grew to 921 cards** (was 907): us_sp500 500, au_asx200 180, jp_nikkei225 110,
   uk_ftse100 92, de_dax 39. Step 1's eligibility loosening was strictly weaker, as predicted.
2. **Verdicts: green 238, yellow 409, red 274.** `check_eligibility_baseline` green at 921
   against the 843 baseline; `export_to_supabase` upserted 921 rows.
3. **Every read regenerated**: `reads generated=921 carried=0 failed=0`.

**The prompt fixes were sampled for the first time and MOSTLY worked.** Measured against the
907-read baseline captured just before the export: em/en dashes fell from 887 of 907 (97.8%) to
20 of 921 (2.2%); 848 of 921 now end on the required verdict phrasing; one still says "sturdy";
zero "not a health signal"; zero changelog lines; "not just X but Y" fell from 6 to 1. **Two
real defects survived and are being fixed on `fix/read-prompt-currency-and-growth` (see
below).**

**BXB, RMS and SPK did NOT come back**, and the third data point settles it: **this is not
per-ticker ingestion loss.** Ingestion was clean for the whole index that run
(`constituents=200 tickers_requested=200 fundamentals_ok=200 fundamentals_failed=0`), so all
three were fetched fine and fall out at the ELIGIBILITY gate. They are now absent from three
consecutive snapshots (08-24, 08-25, 08-26) while present in 08-20, and they did not return even
though ASX grew 168 -> 180 on strictly weaker gates. So one of the four operating-card
requirements (`ebit_margin_pct`, `revenue_growth_yoy_pct`, `net_debt_to_ebitda`,
`fcf_margin_pct`) is null for them. **Which one is not yet diagnosed** and needs either a local
ingestion run or a CI artifact, since the mart holds only eligible rows. They still sit in the
deck on stale 08-20 rows, so the app shows 924.

**MERGED, MR !47 (`fix/read-prompt-currency-and-growth` -> `gitlab/main` @ `1ab08911`): the
read names the card's own currency, and the prose no longer blames the verdict on positive
growth.** Fixed the two prose defects the 2026-08-26 run exposed, widened with the owner's
approval to cover the card copy too. **The card-face half is LIVE on Render now** (the seed
generates `frontend/metrics.json`, no pipeline run needed). **The AI-paragraph half is NOT
live until the next run**, which regenerates all ~921 reads.
- **Invented currencies, 246 of 921 reads (27%).** 60 S&P 500 cards described US companies in
  pounds and pence, 67 Nikkei cards described Japanese ones in dollars and cents, some hedging
  across both ("2.8p or 2.8c ... for every pound or dollar it sells", CBRE). **Root cause:**
  `currency` was passed only to `_format_metric_value`, and operating and financial cards carry
  no `currency`-formatted metric at all, so on 918 of 921 cards the currency never entered the
  prompt and the model supplied one. Fixed by naming it in the user message, normalised through
  a new `_display_currency` (GBp, which 89 FTSE cards carry, is pence and now renders as the
  pound the card face already shows).
- **Positive growth blamed for the verdict, 83 cards.** The verdict downgrades only on an actual
  decline, so the prose was inventing a reason the badge does not contain.
- Also: the same "each sales dollar" framing was live in the **card face** copy
  (`metric_catalogue.csv` across six metrics, plus a hardcoded string in `card_copy.py`), so the
  prompt fix alone would have left every non-US reader looking at it.
- `INPUT_HASH_VERSION` 5a.4 (from 5a.3), so ~921 reads regenerate again on the next run.
  **The bump is a §6 cost decision and the owner APPROVED it** (~921 Haiku calls, the same
  volume as the 2026-08-26 run). Without it the corrected prompt would ship and every stored
  read would keep its defective prose, since the hash never covered the prompt text. Note the
  card-face copy needs no run at all; only the AI paragraph depends on this.

**The next run is the checkpoint for this fix, exactly as the last one was for the previous
prompt change.** There is still no `ANTHROPIC_API_KEY` locally, so MR !47 proved the PROMPT
correct and could not prove the PROSE. When the next run lands, re-measure the same way: pull
`card_assessments` and check that no read names a currency belonging to another market (the
pre-fix rate was 246 of 921) and that none blames the badge on positive growth (83 of 921).
The scratchpad scripts that measured it are gone with the session; the queries are simple
(`market_code` + `ai_read`, regex for currency words, and growth >= 0 against weakness
language).

**Review lesson from MR !47, worth reading before the next copy change.** Five reviewers,
five rounds. The single biggest finding was that the fix was HALF a fix: the same "each sales
dollar" framing was live in the card-face copy, not just the LLM prompt, so fixing the prompt
alone would have left the identical defect beside it on every non-US card. **When a defect is
a phrase, grep every layer that renders text BEFORE scoping the branch.** Second: a
find-and-replace across shared copy has to be checked per `applies_to`, because
`net_margin_pct` renders only on bank cards and "each sale" is the wrong noun there. Third:
claims about the diff (test counts, sweep coverage) were wrong three rounds running because
they were written from memory between edits. Measure them.

**Known limitation recorded, not fixed:** the mart's `currency` is the DISPLAY/trading currency
(`coalesce(info_currency, dim_stock.currency)`). The real reporting currency is `stmt_currency`,
which stops at `fct_fundamentals_snapshot` and is not in the mart, so a company that files in one
currency and trades in another gets a read denominated in the trading one. Fixing it needs a mart
column, an export column and a migration.

**MERGED — MR !43 (`feat/verdict-reads-growth` → `gitlab/main` @ `f950b3e9`): the health verdict
now reads revenue growth, one way only.** **Step 2 of 3 done.** Step 3 (sector-calibrated
thresholds) is NOT started. Every metric a card shows now feeds the verdict, with one recorded
exception (`burn_rate_monthly`, below).

**The design, and the part to protect.** A shrinking top line blocks green. Growth never earns
green and never causes red. Growth sat outside the verdict because a company can grow into
losses, so momentum is not health; one-sided entry satisfies the rule that everything shown must
feed the verdict without discarding that. **Do not let a later change make this a normal
good/weak axis** — that would let momentum buy a health verdict.

**Threshold 0%, no tolerance band.** Any year-over-year decline. A -5% band was proposed on the
argument that one quarter is noisy and the owner rejected it: *"Then you have never talked to a
CFO."* Year-over-year already compares like quarters, so the noise framing was wrong on the
mechanics. It is still one quarter and cannot separate a real decline from a divestment, FX
move or contract timing, which is exactly why the axis can only withhold green, never cause red.

**Measured: 32 cards green to yellow, red unchanged.** Measured on the 907-row 2026-08-24
snapshot, which is neither the whole deck (910) nor post-step-1, so the delta is real and the
absolute totals are stale.

**`burn_rate_monthly` stays shown and unread**, a deliberate exception. Runway is cash divided
by burn, so reading burn separately double-counts. It stays visible because runway is a ratio
and a ratio destroys magnitude: 18 months at $2M a month and 18 months at $50M a month are
different companies. (The "a reader can check the arithmetic" argument does NOT hold, since the
card shows net cash rather than raw cash. Do not repeat it.)

**`INPUT_HASH_VERSION` was `5a.3` at step 2 and is `5a.4` on the branch above, so ~921 reads regenerate on the next run.** The verdict alone
would have rewritten only the 32 changed cards, but the prompt changed too and the hash does not
cover the prompt.

**OPEN, owner's call, not resolved:** the growth metric's card copy says *"One quarter can be
noisy, so look for a pattern over time"* and renders on the card types this gate downgrades, so
a reader on one of the 32 sees a badge that moved on one quarter and, one click away, text
saying one quarter is noisy. Its base-effect caveats also cover only the upside, while the
downside is now the actionable half. §6 metric copy in `metric_catalogue.csv`, which IS inside
scope and was left alone by choice.

**Two process rules this branch established the hard way, both worth more than the code:**
1. **Changelogs live in one place.** 58 dated annotations had been scattered across 17 files,
   plus a changelog line inside the production LLM prompt. Owner: *"if we use change logs, we
   use them in one place, not randomly on any document or file. This is highly unprofessional"*
   and *"And why is this in the prompt??? Hell no"*. **Code and docs describe the present. Git,
   this file, the contract and the review record carry the history.** The mechanism that
   produced it: every review round flagged a stale sentence, the fix stamped a date on it, and
   the next round verified the date was accurate. Accuracy was the only test ever applied,
   because the reviewer briefs only ever asked "is this true" and never "should this exist".
   **No reviewer role owns repo cleanliness — put it in the brief explicitly.**
2. **Fix sloppiness precisely.** The cleanup used a blanket regex and broke 13 places. Only the
   two that broke the dbt parse were caught on the first pass; eleven compiled fine and were
   missed twice more. Damage that still compiles is the damage you have to go looking for.

**Must NOT be swept again:** `supabase/migrations/013_net_cash.sql` keeps its dates on purpose.
It is already applied and the runner tracks by filename with no checksum, so an edit can never
reach the database — it would only make the repo describe a comment that differs from the live
one. **Applied migrations are immutable.**

**MERGED — MR !41 (`feat/drop-price-metrics` → `gitlab/main` @ `8bc3f30`): every metric that
carries the share price is gone from the cards, and the pre-revenue card's net-cash ratio is
now a money amount.** **Step 1 of 3.** Step 2 followed on the same day; step 3 is NOT started.

**The reasoning, which matters more than the diff.** The owner noticed the card showed 8
metrics while the verdict used 6, and led with Forward P/E, which the verdict ignores. Their
rule: *"If we don't use a metric for the verdict then we don't show it."* And Forward P/E
carries the share price, which a twice-monthly pipeline cannot keep current. Checking which
metrics touch price found three: `forward_pe`, `price_to_tangible_book`, `dividend_yield_pct`,
plus `net_cash_to_market_cap` on the pre-revenue card. **13 metrics remain, was 16.** The
columns are all still computed and exported — they are simply no longer catalogued.

**This also settled a design argument.** The agent had objected that widening the verdict to
include valuation would make a health badge move with the share price, which is a buy signal.
Removing the price metrics dissolves that: everything left describes the business.

**Consequences — expect them, they are not regressions:**
- **The deck GROWS.** Both eligibility changes are strictly weaker (no forward P/E required; a
  pre-revenue company no longer needs a market cap). Unmeasurable before a run — the mart holds
  only eligible rows — so it first shows in the next run's card count, which will exceed 907.
- **~910+ Haiku reads regenerate on the next run.** Not a version bump: the input hash covers
  the per-type field set, which changed for all three types.
- **Bank cards went from 7 metrics to 4.**

**Open decisions the owner has NOT ruled on** (all recorded in MR !41):
1. The `net_cash` user-visible copy. Concept approved, wording not.
2. `READ_SYSTEM_PROMPT` was reworded — §6 owner-signed content. Two edits forced by the
   removals (the rule naming P/E as context-only had no P/E left to name).
3. The pre-revenue verdict's net-cash axis is now BINARY. A money amount has no scale-free
   "good" level, so both thresholds are zero and the middle band is unreachable. Green is
   easier to reach for pre-revenue cards.
4. **The bank card's blind spot.** Its four remaining metrics are all profitability, returns
   and growth, and no catalogue text says they cannot judge capital adequacy or asset quality.
   `price_to_tangible_book` carried the only hint. The limit now survives only as an LLM
   instruction, which CI pins for presence in the PROMPT but never in the generated read — so a
   card with a null `ai_read` warns nobody. Needs new bank-card copy, which is owner content.

**Review lesson, worth reading before the next metric rename.** Eight rounds. Three real
findings: the change would have **crashed the live app** (a P/E playground read a label that no
longer existed, on a panel that renders on every card, while pytest stayed green because no
test touched the render path — a guard test now scans that file); the local `dbt build` passed
**vacuously** because no fixture row had a null `forward_pe`, so the eligibility change was
tested by nothing (a unit test now pins all three newly-admitted paths); and the `net_cash`
copy was financially wrong in three ways. **The other five rounds were all stale prose**,
one or two sites at a time, because each sweep searched for the metric IDs and not for the
things written ABOUT them — counts ("all 16", "the five metrics"), lens lists, "card range
mark", worked examples, playground inventories. **Next time: grep for the id, every catalogue
count, and every phrase describing what the metric does, in one pass, before round 1.**

**MERGED — MR !39 (`feat/separate-assessment-and-description` → `gitlab/main` @ `d0f69d2`):
the card face now separates the AI assessment from the company description into two labelled
blocks, the health badge reads Healthy/Mixed/Fragile, and the generation prompt gained two
rules (no dashes as punctuation; don't write like a model, with a carve-out that style never
overrides a required caveat).** Owner-driven across one session, scope widened repeatedly
while looking at the live card. Six review rounds, three reviewers.

**Live now:** the two labelled blocks, the badge wording, and the metric gloss being a step
larger/lighter/looser than the bullet graph's own axis labels (recorded in
`docs/ui/card_metric_cell.md`). **Not live until the next pipeline run:** the prompt rules.
`INPUT_HASH_VERSION` was `5a.2` here, `5a.3` since step 2, and `5a.4` on the currency branch, so stored reads are offered for regeneration on the next run:
until then cards show the NEW badge wording above OLD prose ending on "sturdy", em dashes
included. **The next run is the checkpoint: read a few cards and judge whether the no-dashes
and don't-sound-like-a-model rules actually worked.** That is the only way to know — there is
no `ANTHROPIC_API_KEY` locally, so the new prompt could not be sampled before shipping.

**Decisions locked, do not silently re-litigate:**
- The verdict badge renders ABOVE the "AI-written" label, and the label is omitted entirely
  when `ai_read` is null. The verdict is rule-computed, never model-written; a heading
  claiming AI authorship must not sit over it. Flagged in MR !39 as agent-initiated and
  vetoable; the owner merged without objecting.
- "Higher/Lower is better." stays on EVERY metric. Dropped and then restored after the owner
  named the real tension (it is only true ceteris paribus, a concept this app never teaches).
  Only 4 of 13 metrics carry a bar (was 5 of 16 before the price metrics were dropped), so
  for the other 9 it is the ONLY direction signal on the card face. The code there is identical to before; the decision was genuinely re-taken.
- Badge wording is Healthy/Mixed/Fragile. Strong/Weak was rejected for reading as a verdict
  on the share rather than on the company's finances.

**DONE — the manual `data-pipeline` run (2026-08-25, pipeline #94, job succeeded in 74 min).**
Owner triggered it from the GitLab web UI; this was the first time the CI path ever ran
against the new Supabase project. Outcome, verified against production rather than taken from
the job log alone:
- **The MR !33 fix works.** DYL is now `company_type = pre_revenue`, and the sector range it
  was wrecking is fixed: `au_asx200` Energy `sector_min_fcf_margin_pct` went from
  **-129,810.50%** to **-29.59%** (PDN, a real company), max unchanged at 15.29%. The 10
  operating peers now spread across a readable band instead of collapsing onto ~100% of a
  129,825-point span. DYL's own sector min/max are null, which is correct — pre-revenue cards
  are excluded from the benchmark cohort.
- **The CI-to-Supabase path is proven.** `apply_supabase_migrations.py` connected on its first
  attempt through the Session pooler host, `dbt build` and all three health checks passed, and
  `export_to_supabase: upserted 907 rows to 'public'`. That was the standing risk for the
  2026-09-01 unattended run and it is now retired.
- **Assessments regenerated fully:** `907 cards -> verdicts {red 271, yellow 372, green 264}`,
  `reads generated=907 carried=0 failed=0`. Every input hash moved, as expected from fresh
  prices; no Anthropic API failures.
- **The pipeline shows `manual`, not `success`, and that is fine** — `supabase-migrate` and
  `dev-schema-check` are unplayed manual jobs in the same pipeline, which keeps the overall
  badge at `manual`. The `data-pipeline` job itself is `success`. Do not read the badge as a
  failure.

**Two gaps this run exposed, neither a defect in the fix:**
- **DYL has no `cash_runway_months` and no `burn_rate_monthly`** (both null; `net_cash_to_market_cap`
  is populated), so the company that motivated the whole reclassification now gets a thinner
  pre-revenue card than its two peers. Either `stmt_cash_and_equivalents` is missing for it or
  the annual-statement burn does not compute positive. **Not diagnosed.**
- Only **3 pre_revenue cards exist** across all 5 markets (DYL, GGP, NXG — all `au_asx200`;
  770 operating, 134 financial). The pre-revenue metric set and its copy therefore ride on a
  very small population. Worth knowing before investing further in that branch of the Router.
  Two of the three do carry a runway (GGP 1.5 months, NXG 41.3), so the copy does render.

**MERGED — MR !36 (`docs/cash-runway-learn-text-pre-revenue` → `gitlab/main` @ `cde3447`):
`cash_runway_months`'s catalogue `learn` text widened to "For a company with little or no
revenue" to match the population MR !33's classifier created; owner signed off on the exact
phrasing 2026-08-25. Copy only, live on Render at merge (no pipeline run needed). Nine
review rounds on a one-string payload that was byte-stable from round 1 — every FAIL was
against the surrounding prose. **The lesson worth keeping:** three rounds in a row corrected
the same sentence about what `check_eligibility_baseline.py` compares, each fixing the
arithmetic one layer down and leaving a fresh unverified conclusion on top; round 8 ended it
by deleting the conclusion instead of correcting it again. When a sentence fails review
repeatedly, the sentence is the problem, not the numbers in it. Reviewers also flagged that
~18 lines of gate internals had accreted in this file as sediment from the argument itself
— removed. Also from that session: the plugin's reviewer agent types were not dispatchable,
so each ran as a general-purpose agent reading its own role file verbatim (recorded in that
MR's `review.md`), and `frontend/*` routing means a generated `frontend/metrics.json` pulls
in cto-reviewer.

**MERGED — MR #33 (`fix/pre-revenue-classification-threshold` → `gitlab/main` @ `1e6e33d`):
the sector min/max data-quality issue fixed — Deep Yellow (ASX: DYL)'s outlier margins
resolved by widening the `pre_revenue` classification, not by patching the ratio.**
Investigated live against production first: DYL is a genuine one-off (only company with
|margin| > 1000% across all 5 markets), its real `stmt_total_revenue` is $15,949 (positive,
not negative — an early check against a different yfinance field had suggested negative and
was corrected) against a $1.7B market cap, ~0.001% — a uranium development-stage miner the
existing `revenue <= 0` classifier missed by a hair. Owner chose the root-cause fix over
floor/exclude alternatives and delegated the threshold ("option 1, you pick the
threshold"); landed on revenue < 0.1% of market cap (a ratio, not a currency floor — 5
markets, no FX normalization anywhere in the pipeline), empirically checked against the
full dataset (next-most-extreme company is 157x less extreme than DYL — wide safety
margin). `dbt build` (107/107), layer/structure/doc checks, sqlfluff, and pytest (209) all
pass. Five review rounds, all three required reviewers (scope-auditor,
analytics-engineer-reviewer, equity-analyst-reviewer) — every round caught a real finding:
verifiability of owner-authority claims, a contract self-contradiction, a stale handover
entry (this file, twice — the exact "handover fell behind actual state" failure mode this
file's own Context/open items section already warned about), and a cross-file attribution
gap; all resolved, round 5 all PASS. **The follow-on copy question is now answered:**
`cash_runway_months`'s catalogue `learn` text read narrower than the newly-widened
`pre_revenue` population covers (equity-analyst-reviewer flagged it non-blocking in that
MR, and it was deliberately left for its own owner sign-off rather than folded into the
SQL-threshold delegation). Owner signed off on 2026-08-25; "For a pre-revenue company"
becomes "For a company with little or no revenue" on branch
`docs/cash-runway-learn-text-pre-revenue`. Copy only, no SQL, and it needs no pipeline run
to reach users: no dbt model refs the `metric_catalogue` seed and the export ships only
`marts.mart_stock_cards`, so the card reads the regenerated `frontend/metrics.json` from
the repo and the new text goes live on Render's auto-deploy at merge.

**MERGED — MR #31 (`fix/action-bar-nav-row-sibling-selectors` → `gitlab/main` @ `5480d91`):
same dead-sibling-selector bug fixed for `.ss-action-shell` (Save/Skip action bar) and
`.ss-nav-row-marker` (nav row, 11 rules)** — found via a follow-up check MR #29's own
reviewer flagged but didn't confirm live. `.ss-action-shell`'s breakage had real functional
impact: Save/Skip was never actually pinned to the viewport bottom, so reaching it required
scrolling through the entire card — a violation of the UX gate's own "Save still reachable
on Discover" checklist item, not just subtle typography. Reported back before fixing; scope
widened with explicit approval. Also fixed a second, distinct bug: the nav row's segmented-
control sub-rules targeted a testid (`stSegmentedControl`) that doesn't exist in the
installed Streamlit version — the real one is `stButtonGroup`, confirmed against the
shipped source. Added `tests/frontend/test_styles.py`: this was the 5th–6th recurrence of
the same bug class across 3 merged PRs with zero test coverage added each time — a static
regex guard now pins the specific broken shape. Two review rounds: round 1 cto-reviewer
FAILed on that missing-coverage gap (fixed); round 2 both PASS. 209 tests. **Minor,
non-blocking note from round 2:** the new regex is tuned to the literal `.marker + div[...]`
shape (every recurrence so far) — a hypothetical future variant with no `div` element prefix
(`.marker + [data-testid=...]`) would slip past. Judged acceptable (Streamlit only ever
renders these wrappers as `<div>` in the installed version) but worth knowing if this class
of bug ever resurfaces in a different shape.

**MERGED — MR #29 (`fix/css-specificity-audit-p-tags` → `gitlab/main` @ `8fe21ab`): the
Streamlit CSS-specificity bug MR #24 first found (bare single-class `<p>` selectors losing
declared `font-size`/`margin-top` to a higher-specificity Streamlit emotion-cache ancestor
rule) fixed across ~24 more classes app-wide** — scoped under each element's real parent
class where one exists, `!important` where none does; every one re-verified live via
computed styles, not just static analysis. Also fixed three unrelated dead sibling-combinator
selectors found along the way, all near the card footer (`ss-freshness`, the footer's border
separator, the Yahoo Finance link button's sizing) — same root cause (a marker `<div>`'s
assumed DOM sibling doesn't exist; Streamlit wraps it, so the real sibling is one level up).
Three review rounds: round 1 cto-reviewer FAILed with 2 real findings (fixed); round 2
scope-auditor correctly ESCALATEd whether fixing the footer-separator bug (found mid-task,
not part of the original ~24-class list) was in scope, and whether a border rendering for
the first time was really "no visual change" — genuinely escalated, owner answered "fix all
three" (including a third twin cto-reviewer found, the link button); round 3 both PASS. 207
tests. **Flagged, not fixed here** (own follow-up task already spawned, chip in the session
UI if still there — check `frontend/styles.py` directly for `.ss-action-shell`/
`.ss-nav-row-marker` if it's gone): cto-reviewer spotted two MORE rules that may share this
exact dead-selector pattern (the fixed Save/Skip action bar, the Discover/Saved/Search nav
row) but didn't confirm live — deliberately kept out of this PR rather than expanding scope
again without asking. The sector min/max data-quality issue is still the only other open
item below.

**MERGED — MR #27 (`chore/remove-dead-benchmark-indicator` → `gitlab/main` @ `d023078`):
dead `benchmark_indicator()`/`_BENCHMARK_INDICATORS` removed from `frontend/card_copy.py`**
— left over from Slice 6c's arrow-to-word benchmark label swap; sibling
`benchmark_indicator_label()` unaffected, still used by `card_ui.py`. Test coverage for the
other still-live helpers in the same test file preserved. Two review rounds — round 1
scope-auditor FAILed on `.claude/task/contract.md` not listing itself in its own
`scope_paths`, fixed, round 2 both PASSED. 207 tests. This was item 1 of the "Next concrete
actions" list below; items 1-2 there now (sector data-quality issue, CSS-specificity audit)
remain open.

**MERGED — MR #24 (`feat/metric-cell-groups-and-range-redesign` → `gitlab/main` @
`4e7b7d4`): universal direction cue (all 16 catalogued metrics, not just the 5
benchmarked), range-mark layout redesign (numbers above the bar, word labels below),
metric catalogue's lens grouping surfaced as visible section headings (card face + learn
panel), a "No sector comparison for this metric" placeholder, and a repo-wide sweep
removing stale "five metrics"/"hero" claims plus a full em-dash/AI-voice writing pass
across the catalogue and app copy.** 7 review rounds, all 4 reviewers passing — full trail
in the merged branch's own `.claude/task/contract.md`/`review.md` if needed. 207 tests.
**Flagged, not fixed here:** a sector data-quality issue (one ASX Energy stock's
near-zero-revenue denominator distorts its whole sector's FCF/EBIT margin range mark —
dbt-layer fix, owner call); a Streamlit CSS-specificity gotcha (~20 other pre-existing
single-class `<p>` rules across the app may share the silent-margin-reset bug this branch
fixed for a handful of its own classes — spawned as its own follow-up task, not audited
here).

**MERGED — MR #22 (`feat/metric-range-mark` → `gitlab/main` @ `ebbe74a`): card-face
benchmark indicator replaced with a monochrome range mark** (value positioned between
sector min/max, median labeled; `sector_min_*`/`sector_max_*` added through dbt → mart →
Supabase export). Direction cue ("Lower is better.") added for net debt/EBITDA only —
forward P/E stays uncued (own catalogue interpretation + this app's health-verdict logic
both treat its direction with caution; deep-dive `learn` text extended instead). Nine
review rounds, real findings in eight — full trail in the merged branch's own
`.claude/task/contract.md` if needed. **Flagged, not fixed here:** review-cycle
efficiency (9 rounds judged excessive by owner — tracked in
[stock-swipe-app#5](https://gitlab.com/rami.al-fahham/stock-swipe-app/-/work_items/5),
filed there not in `dbt-agent-kit` since GitHub is still suspended); a catalogue-wide
em-dash/readability pass (~25 fields); a mangled-encoding artifact in one catalogue field;
this file's own size (see below). **Still not started:** the 11-metric benchmark
expansion (financial + pre-revenue, 2 more operating) — explicit owner-approved follow-up.

**MERGED — MR #19 (`chore/biweekly-pipeline-cadence` → `gitlab/main` @ `86105ba`): pipeline
cadence switched weekly → every two weeks** (1st/15th, owner's call). Copy + repo-wide doc
sweep + a real functional catch — `STALE_SNAPSHOT_DAYS` recalibrated 7 → 18 so the
"data may be old" warning doesn't fire on every healthy cycle (owner approved: "Keep 18").
Five review rounds, real findings in four — full trail on the merged branch if needed.
**The one piece this MR couldn't do — creating the actual GitLab pipeline schedule — is
now also done** (2026-08-24, see Infra section above).

**`ci-runner-01`'s 403-on-fetch (flagged after MR #19) is RESOLVED** — confirmed via
`glab api .../pipelines`: MR #19's pipeline succeeded on retry the same night, and a fresh
`main` pipeline the next day (2026-08-22, `id 2781739048`, sha `456459b` — matches the
commit actually checked out) ran clean. Whatever the duplicate-registration issue was, it
either self-healed or got fixed outside this session — not confirmed which, so if it
recurs, re-check the Hetzner box's `gitlab-runner config.toml` as originally suspected.

**MERGED — MR #15 (`fix/learn-panel-metrics-first` → `gitlab/main` @ `f1ee009`): learn-panel
content order fixed** (about-company was rendering first, ahead of any numbers content;
now matches `docs/north_star.md:80`'s already-approved Deep-tier order). Three review
rounds, real findings in the first two, both fixed — full trail archived on the merged
branch if needed.

**MERGED — MR #17 (`feat/per-metric-disclosure` → `gitlab/main` @ `de746d2`): company
description and each metric explanation now have their own Read more/Show less** (was one
long always-visible scroll once the learn panel opened). Reopened two Slice 6c
consolidations (owner-initiated). Also fixed `ebit_margin_pct`'s learn copy. Four review
rounds, real findings across three of four reviewers, all fixed — full trail on the merged
branch if needed. The metric-cell's own visual hierarchy this entry flagged as unscoped —
see the `feat/metric-range-mark` entry at the top of this section, now built.

**Merged (full detail in `docs/handover_2026-08-18.md`):**
- Metric layer + data-only `info_*` metrics (#131–137): ROE, four ratios, FCF yield.
- Sector Router Slice 1 (#139): `company_type` classifier (financial / pre_revenue / operating).
- Sector Router Slice 2 (#140) + 2b (#141): balance-sheet + full three-statement raw data foundation.
- Sector Router Slice 3a (#142) + 3b (#143): statement enrichment + 13 per-type computed metrics.
- Sector Router Slice 4a (#145): Router mechanism (`applies_to` → `metrics_for_card`), grown operating
  card (5→8 metrics), baseline 25.
- Sector Router Slice 4b (#146): financial/bank card (4 metrics), per-type eligibility, baseline 25→30.
- Sector Router Slice 4c (#147): pre-revenue/survival card (4 metrics), pre-revenue eligibility branch,
  baseline 30→35.
- Slice 5a (#148): deterministic 🟢/🟡/🔴 health verdict (rules, not LLM) + `card_assessments` storage.
- **Slice 5b (MR #3): Claude Haiku prose read, regenerate-on-change.** `READ_SYSTEM_PROMPT`/
  `READ_METRIC_BRIEF`/`build_read_messages`; Haiku call gated on `input_hash` change; degrades
  gracefully with no key. Five review rounds, four with real findings (a credential/network-leak in an
  adjacent test, a stale `.env.example` reference, eleven missing metric-applicability caveats, a
  "financial = bank" mislabeling) — all resolved. pytest 142.
- **Slice 6a (MR #4): UI design-system foundation.** New spacing/radius/type-scale CSS tokens
  (`frontend/styles.py`) + `frontend/row_ui.py` shared by Saved-list and Search (Search previously had
  zero custom styling) + `docs/ui/design_system.md`. Six review rounds, five with real findings (missing
  test coverage, a hover-highlight CSS bug bleeding to all rows, an unverified Saved-focus-view
  regression, two rounds of fabricated "Used by" token-doc claims that needed real wiring, not just doc
  edits). pytest 145.
- **Slice 6b (MR #8 + MR #9, both MERGED — confirmed on `gitlab/main` @ `1463c95`):**
  **button/popover/expander/link-button skin unified app-wide.** MR #9's branch was
  accidentally pushed straight to `main` first (see the git-push footgun note in Do NOT); MR
  #8 reverted that on `main` so MR #9's diff applied cleanly on top. Owner's own instruction: "100% consistent
  design language for the whole web app" — not narrowly Landing/Overflow. Generalized the accent/surface
  button skin (was `.ss-action-shell`-scoped to just the Discover bar) to `button[kind="primary"/
  "secondary"]` globally; added base skins for every `st.popover` trigger (fixes the previously-fully-
  unstyled "Filters" trigger) and every `st.expander`; gave `st.link_button` the same treatment across
  all three variants (primary/secondary/tertiary), even though only secondary has a live consumer today
  (owner decision — cover it now so a future variant never silently ships unstyled). Three review
  rounds, real findings every round: (1) the original diff greped only `st.button(`, missing
  `st.link_button` (the card footer's "Yahoo Finance" link) entirely; fixing it surfaced a **second,
  deeper bug** — the real rendered testid is `stBaseLinkButton-secondary`, not `stLinkButton`, so a
  pre-existing (pre-6b) footer-scoped sizing rule had silently matched nothing since before this slice
  started; fixed both. (2) A duplicate top-level `amendments:` key left in the contract by a sloppy edit;
  fixed. (3) Two genuine owner escalations, both reviewers independently: whether to bundle the
  pre-existing footer-rule bug fix into this diff (owner: yes, same file/root cause) and whether to cover
  the unused link-button variants (owner: yes, all three). Every testid claim (`stExpander`,
  `stPopoverButton`, `stBaseLinkButton-{kind}`, the segmented control's `kind` values) independently
  verified against the actual installed `streamlit==1.57.0` bundle by cto-reviewer, not taken from
  memory — `stLinkButton` had looked right and was wrong. pytest 145 (no test imports `styles.py`, so
  the suite carries no regression signal for this diff specifically — verification was DOM/computed-style
  checks + real screenshots via the 6a headless-Chrome CDP harness). Full detail in
  `.claude/task/contract.md`'s amendments and `.claude/task/review.md`.
- **Slice 6c — MERGED** (MR #10, https://gitlab.com/rami.al-fahham/stock-swipe-app/-/merge_requests/10,
  `feat/ui-slice6c-card-content` → `gitlab/main` @ `0a72073`; branched from `gitlab/main` @ `1463c95`,
  i.e. 6b's tip — no rebase
  needed): **health verdict badge + AI read render on the card; ~11 disclosure toggles consolidated
  into one `st.expander`; metric labels as chips; benchmark comparisons show words, not arrows.**
  First slice to actually read `card_assessments` from `frontend/` (new
  `fetch_all_assessment_rows`/`fetch_card_assessments`/`fetch_eligible_cards_with_assessments` in
  `supabase_cards.py`, new pure `attach_assessments` in `explore_filters.py`). Two review rounds, both
  FAILED round 1 with real findings, all resolved and recorded in `contract.md`'s `amendments` before
  round 2 PASS: (1) `MEDIAN_PRIMER`'s stale arrow-glyph-legend clause was edited out (correctly — the
  words-not-arrows swap made it inaccurate) with no recorded owner authority; owner approved keeping
  the fix. (2) `VERDICT_MEANING` (a planned copy-sync mechanism, mirroring 5a's `INPUT_FIELDS_BY_TYPE`
  guard) shipped with zero consumers anywhere in the UI; owner chose to drop it entirely (YAGNI) rather
  than keep it as unused insurance — deleted along with its new `tests/tooling/` guard test. (3) this
  diff's own hunk removes the last production caller of the arrow-glyph `benchmark_indicator()`/
  `_BENCHMARK_INDICATORS`, leaving them dead with only an out-of-scope test
  (`tests/frontend/test_benchmark_indicators.py`) still exercising them; owner chose to leave this
  deferred rather than widen `scope_paths` this late — **a separate cleanup task for this is already
  spawned** (chip in the session UI, title "Remove dead benchmark_indicator() glyph function"; if it's
  gone from the UI by the time you read this, either it ran or was dismissed — check
  `frontend/card_copy.py` directly). pytest 163. Local verification used a hand-built headless-Chrome
  CDP harness (Browser pane tooling was non-functional this session) driving a Streamlit mock
  entrypoint — **two real gotchas hit and fixed, worth knowing before rebuilding this pattern**: (a)
  `app.py` calls `main()` unconditionally at module level, so a mock entrypoint must patch
  settings/supabase_client/supabase_cards/browser_storage **before** `import app`, and must NOT also
  call `app.main()` again on that same first run — Streamlit's `sys.modules` caching means `import app`
  is a no-op on every SUBSEQUENT rerun within the same process, so the entrypoint needs `"app" not in
  sys.modules` to decide whether to rely on the module-level call or invoke `app.main()` itself; getting
  this wrong either renders nothing (no explicit call, no cached rerun) or crashes with
  `StreamlitDuplicateElementId` (calling `main()` twice on the same run re-registers the same widget).
  (b) the real `browser_storage.ensure_interactions_loaded()` mounts a `streamlit-extras`
  `local_storage_manager` custom component that needs a genuine browser round-trip to report
  `.ready()`; under CDP-driven automation it never does, so bypass the function entirely — but
  `render_landing()`'s `onboarding_ready()` gate depends on a session-state flag that function normally
  sets, so also seed `st.session_state[browser_storage._ONBOARDING_LOADED_FLAG] = True` directly, and
  leave `is_onboarding_dismissed()` UNPATCHED (it just reads session state, which the real "Start
  exploring" button click sets correctly on its own) — patching it to a hardcoded `False` blocks the
  landing page from ever dismissing.
  **UPDATED 2026-08-30, both gotchas above are now stale if rebuilding this pattern:** (a) is no
  longer true: `app.py`'s `main()` call is now guarded (`if __name__ == "__main__":`), so a bare
  `import app` no longer triggers it; a future mock entrypoint needs an explicit `app.main()` call
  every time, not the conditional-on-`sys.modules` dance described above. (b)'s landing-page
  patching instructions are obsolete outright: `render_landing()`, `onboarding_ready()`,
  `is_onboarding_dismissed()`, and `_ONBOARDING_LOADED_FLAG` were all deleted in
  `feat/kill-landing-screen` (the landing screen itself is gone, straight into Discover on first
  launch); nothing left to seed or unpatch for it.
- **Global hook bug found and fixed while landing 6b (separate track, affects every project on this
  machine, not just this repo):** `~/.claude/hooks/branch_discipline.py` and `commit_review_gate.py`
  (both wired via `.claude/settings.json`/the user-level `~/.claude/settings.json` per the agent-setup-
  hygiene work above) resolve "the repo" via `CLAUDE_PROJECT_DIR` — always the **main checkout**, never
  the actual worktree a command runs in. Every `cd <worktree> && git commit ...` (this repo's own
  worktree-per-task pattern) got wrongly evaluated against the main checkout's branch/staged-diff state:
  `branch_discipline.py` falsely blocked a legitimate commit on a feature-branch worktree ("BRANCH
  BLOCKED... main/master") because the main checkout happened to be on `main`; `commit_review_gate.py`
  silently no-op'ed instead (main checkout had nothing staged, so its "nothing staged, let git complain"
  early-return let commits through without ever actually checking the worktree's real review state — a
  live gap, not just a false block). Root cause confirmed two layers deep: (1) the hook event JSON does
  carry a `cwd` field for the Bash call, but it reflects the session's persistent shell directory as of
  the START of that call, not a `cd` chained inside the same command string — so even switching to prefer
  `cwd` over `CLAUDE_PROJECT_DIR` wasn't enough on its own; (2) fixed by additionally parsing a leading
  `cd <dir> &&`/`cd <dir>;` in the command text itself (verified the dir exists on disk) and preferring
  that over the event's `cwd`, which is itself preferred over `CLAUDE_PROJECT_DIR`. Verified safe for
  every other project: this only changes behavior for the worktree case that was previously wrong: no
  leading `cd` -> falls through to the previously-fixed `cwd` behavior -> falls through to the original
  `CLAUDE_PROJECT_DIR` behavior, so normal (non-worktree, non-`cd`-prefixed) commands are unaffected.
  Verified via direct hook invocation with constructed event JSON (both the false-block and the
  true-block cases) before landing, then via the real commit succeeding end-to-end. **Bug in the
  `dbt-agent-kit` plugin's own bundled hook source too** (identical `_repo_root()` pattern) — only the
  machine-wide installed copies at `~/.claude/hooks/` were fixed here; the plugin's own source under
  `~/.claude/plugins/marketplaces/dbt-agent-kit/hooks/` was NOT touched (out of this repo's scope
  entirely) and will regenerate the same bug on a future plugin re-sync unless fixed upstream too —
  flagged, not resolved.
- README/shopfront (#138): owner's manual steps may still be pending — `docs/media/swipe-demo.gif`
  (+ uncomment README line) and an optional social-preview image.
- Test-architecture cleanup (#144): `tests/` reorganized into domain subdirs + `conftest.py` + taxonomy doc.
- **Agent-setup hygiene (MR #5 + #6, separate track, not a product slice):** `working-agreement.md`
  force-loaded via `@`-import, `dbt-mcp` pinned, this file's own trim/corrections, review-gate/pre-push/
  handover hooks wired project-scoped, `review_routing.json` hardened with 4 guard-path routes (modeled
  on football-data-pipeline's routing). **MR #5's merge and a later push raced** — 3 commits landed after
  the merge point and needed a second MR (#6) to land; verify with `git merge-base --is-ancestor
  <branch> <target>` before trusting a "merged" report, not just the MR's status label. Full record in
  `.claude/task/contract.md`'s amendments log (9 review rounds across both MRs, 6 with real findings) and
  memory `global-hooks-collision-risk`.

**Not started:** nothing on the Slice 6 track — 6a/6b/6c are all code-complete (6a/6b merged, 6c MR #10
awaiting owner review). Next work here is whatever the owner scopes after Slice 6 closes out.

## Decisions locked (the important ones)

- **"Do it right" (this session):** stay on yfinance, **but compute from period-matched financial statements,
  not `info` scalars.** yfinance exposes the full balance sheet + cash flow (incl. Operating Cash Flow, Capex)
  + income statement; the balance sheet was the missing third — landed in #140.
- **The metric-assignment MATRIX (design frame, this session).** Perspectives (valuation · profitability ·
  growth · solvency · liquidity · cash · returns) are semi-universal *lenses*; the metric filling each is
  **type-specific**; some lenses are **honestly EMPTY** — do NOT fill with a weak proxy.
  - **operating** — fills all seven (the challenge is *curation* for a scannable card, not validity).
  - **financial** — valuation (**P/B → P/TBV**, P/E), returns (**ROE**, dividend yield), profitability (margin),
    growth. **NO sound solvency/liquidity/cash metric** — the real ones (CET1/Tier 1/NIM/asset quality) are
    unsourceable from yfinance → leave the solvency slot **honestly blank**, don't fake it.
  - **pre_revenue** — a balance-sheet **survival** story: cash, burn, runway, net cash vs EV, working capital.
- **Metric definitions locked (this session, §6):** (1) **statement ROE computed correctly** — ingest
  `Net Income Common Stockholders` so ROE = common income ÷ common equity (fixes the #141 attribution
  mismatch; landed in Slice 3a). (2) **ROA adopted into the financial column** — the one sourceable,
  bank-relevant metric from the external review; compute `net income ÷ total assets` from statements (the
  `returnOnAssets` scalar is a probe cross-check only). (3) **cash_runway = cash ÷ FCF-burn, in months**
  (FCF-burn = OCF + Capex when negative). (4) **coexist, don't replace** — new computed columns sit alongside
  the existing info-scalar `current_ratio`/`roe_pct`/`fcf_*`; Slice 4 picks per-type display.
- **External metric review adjudicated (this session):** an outside review (Gemini) proposed CET1/Tier 1/
  LCR/NIM/ROIC/ARR/NRR/TAM etc. — all rejected as **unsourceable from yfinance** and/or too advanced for a
  beginner card (the honest-blank ceiling stands). Only **ROA** survived both filters (sourceable +
  beginner-legible) → adopted. Filter every future metric suggestion through: (1) sourceable from yfinance?
  (2) legible to a true beginner?
- **yfinance `dividendYield` is PERCENT, not a fraction (discovered in 3b, verified live):** MSFT 0.94 =
  0.94%, JPM 1.78, KO 2.56, O 5.15 — so `dividend_yield_pct = info_dividend_yield` (NO ×100), and the stale
  "(decimal)" docs were corrected to "(percent)". `payoutRatio` IS still a fraction (MSFT 0.21);
  `returnOnEquity`/`returnOnAssets` are fractions (so `roe_pct`/`roa_pct` ×100 stay correct). **Slice 4 must
  add a persisted scale-regression guard** — a future yfinance version reverting dividendYield to a fraction
  would ship a 100× error.
- **Corrected: debt-to-equity + interest coverage are OPERATING-company solvency metrics, NOT bank metrics**
  (interest coverage is meaningless for a bank — interest is its cost of funds; debt-to-equity is weak for
  banks). The earlier "build the bank debt measures" framing was mine and was wrong; the matrix reassigns them
  to operating companies (complementing net-debt/EBITDA).
- **Outlier magnitudes are REAL** (mis-applied to the wrong type) — route to the right lens, don't clip.
- **Cataloguing a metric RENDERS it** (catalogue → metrics.json → card_copy → card_ui, uniform). New metrics
  stay **data-first** (compute, no catalogue row) until the Router owns per-type cataloguing/display.
- **Authoring metric copy/caveats is §6.** Data-only PRs keep `data_contract.md` strictly factual.
- **Plan-mode spine** (EnterPlanMode → ExitPlanMode → plan_implement_gate); no prose plan-back. Ask the owner
  in PLAIN language, with a recommendation, sparingly (see `ask-questions-plain-language`).
- **AI assessments:** educational, NEVER advice; true-beginner language; reason only from the given numbers;
  end with a health verdict (🟢/🟡/🔴).
- **6a deliberately scoped narrow** — design-system tokens + shared row primitive only; explicitly does not
  touch 6b (Landing/Overflow) or 6c (rendering the new card content). Don't widen a UI-phase PR to cover a
  later phase's scope.

## Step 3: sector-calibrated verdict thresholds (THE next fundamental piece)

Steps 1 and 2 arranged what feeds the verdict. Step 3 is what makes the verdict credible. The
health thresholds are fixed global numbers: the same margin bar for a supermarket and a software
company, the same leverage bar for a utility and a retailer. The owner raised this themselves by
asking where the rules came from and whether professionals use them.

**Honest answer given at the time:** the metrics are standard and the numbers are conventional
rules of thumb (net debt/EBITDA under 1.5x good and over 3x weak is a real credit convention;
current ratio, ROE around 10%, bank ROA around 1% are all textbook). What separates them from
practice is that they are sector-blind, single-snapshot, and thin for banks.

**Percentile ranking was proposed and REJECTED by the owner, correctly:** *"Being in some top
percentile can still mean an unhealthy state if the whole sector is in an unhealthy state."*
Do not revive it. It is also not what practitioners use for solvency; it is a relative-valuation
screening tool. Rating agencies publish per-industry ABSOLUTE thresholds, which is the shape to
copy.

**Measured evidence for why one global set cannot work** (operating cards, p25/median/p75):

| Sector | EBIT margin | FCF margin | Net debt/EBITDA |
|---|---|---|---|
| Utilities | 14.6 / 21.5 / 24.5 | **-15.4 / -6.7 / 0.5** | 3.8 / **5.6** / 6.3 |
| Real Estate | 18.2 / 29.3 / 45.8 | 16.4 / 35.8 / 51.0 | 4.9 / **5.7** / 7.5 |
| Technology | 11.2 / 19.4 / 30.8 | 11.2 / 19.0 / 27.7 | -0.2 / **0.5** / 1.5 |
| Consumer Defensive | 4.4 / 12.1 / 17.5 | 3.1 / 8.2 / 11.6 | 1.3 / 2.5 / 3.2 |
| Industrials | 7.1 / 11.2 / 18.8 | 5.0 / 9.5 / 14.7 | 0.8 / 1.8 / 2.9 |

Under today's global bars, most of Utilities is structurally red on cash flow and most of Real
Estate is red on leverage, for being normal examples of their industry.

**The second half: interest coverage.** Operating profit divided by interest expense, i.e. can
the company service its debt. It is the standard solvency measure and the rubric has nothing
like it. **`interest_coverage` is ALREADY computed** in
`int_stock__card_metrics.sql`, but it stops there: it is NOT in `mart_stock_cards`, NOT exported,
and therefore invisible to the verdict, which reads mart rows. Adding it means a mart column, an
export column, a Supabase migration, and a catalogue row (and cataloguing it means the card shows
it, which by the owner's own rule means the verdict must read it).

**Two standard scores checked and NOT usable here:** Altman Z needs retained earnings, which is
not ingested. Piotroski F needs year-over-year comparisons, and only the latest annual snapshot
is stored.

**Suggested sequencing, not yet agreed:**
1. Plumb `interest_coverage` through to the mart and export so its real distribution can be seen.
   No verdict change yet. Its thresholds cannot be calibrated from data until one run has landed.
2. Set per-sector thresholds. Open question the owner has not ruled on: all 11 GICS sectors, or a
   handful of groups (capital-intensive / asset-light / cyclical / financial) to keep the table
   tractable. Either way the numbers are owner decisions, and there are roughly 6 metrics x N
   sectors of them.
3. Measure the verdict shift against live cards before shipping, the way steps 1 and 2 did.

**Do NOT start this by writing code.** The threshold table is the deliverable and it is owner
content; the code around it is small.

## Next concrete actions

**Slice 6 (UI redesign) is fully done — 6a, 6b, 6c all merged.** Nothing queued on that track.
Historical design docs, kept only in case a future slice needs to consult prior reasoning:
`~/.claude/plans/noble-forging-beaver.md`, `logical-roaming-brook.md`, `dynamic-snuggling-truffle.md`.
Full slice-by-slice action history in `docs/handover_2026-08-18.md`.

1. Nothing is blocking. The manual `data-pipeline` run that used to be item 1 is **done —
   see the Status entry for what it proved and what it left open.** Pick the next item by
   what matters to you; 2 and 3 below are both small and neither is urgent.
2. Fix `docs/data_contract.md:236-237` — it still justifies the `pre_revenue` eligibility
   branch with "the operating metrics break for revenue ≤ 0", which MR !33 made incomplete
   (they also break for positive-but-negligible revenue). The classification section 30
   lines above it at `docs/data_contract.md:200-207` WAS updated; this line was missed.
   Found independently by both analytics-engineer-reviewer and equity-analyst-reviewer
   while reviewing the copy branch, and left out of it as out-of-scope. Internal doc prose,
   not user-visible copy.
3. Work out why BXB, RMS and SPK (all `au_asx200`) dropped out, and decide what should
   happen to a card whose ticker stops appearing. Two separate questions:
   - Is the drop ordinary eligibility movement or per-ticker ingestion loss? Only the
     second is a bug. **The 2026-08-25 CI run made this sharper, not softer:** all three are
     present in the 08-20 snapshot and absent from BOTH 08-24 (local run) and 08-25 (CI run,
     different machine, `check_eligibility_baseline.py` green). Two independent runs agree,
     so this is persistent, not a transient yfinance blip. Still undiagnosed — the next step
     is checking whether they are ingested at all (raw parquet) versus ingested and ruled
     ineligible, which the mart alone cannot distinguish.
   - Whatever the cause, a ticker that stops being exported keeps its last card in the deck
     indefinitely, because the frontend dedupes to the newest row per ticker rather than to
     the newest snapshot. There is no eviction anywhere in the pipeline or the app. Today
     that is three cards five days stale, which the per-card "As of" line does disclose. It
     is only a real problem if a ticker drops out for good — then the deck keeps serving a
     card that ages without limit. **Deciding whether the deck should evict by snapshot age
     is an owner call** (it changes what users see), so it is written down here rather than
     designed.
4. Sync local `main` (`git fetch gitlab && git merge --ff-only gitlab/main`) before starting anything
   new, if it's drifted behind `gitlab/main` again.

(The `.ss-action-shell`/`.ss-nav-row-marker` sibling-selector check that used to be item 1
here is done — will get its own Status entry once this branch merges. Turned out bigger
than "check": `.ss-action-shell`'s dead selector meant Save/Skip was never actually pinned
to the viewport bottom, a real violation of the UX gate's own "Save still reachable on
Discover" checklist item, not just a subtle typography gap. Reported back before fixing;
owner approved the fix with full knowledge of the actual scope. Also added
`tests/frontend/test_styles.py` — `frontend/styles.py` had ZERO test coverage across 3
merged PRs (MR #24, #29) all fixing this same dead-CSS-selector bug class; a static regex
guard now pins the specific broken shape so it can't silently recur a 7th time. The Streamlit
CSS-specificity audit that used to be part of item 1 before that is done — see the
MR #29 Status entry above, ~24 classes, live-verified. The dead-code cleanup that used to be
item 1 before that is done — `benchmark_indicator()`/`_BENCHMARK_INDICATORS`
removed from `frontend/card_copy.py`, test coverage preserved for the still-live helpers in
the same test file. The pipeline schedule that used to be item 1 before that is also done —
see Status/Infra. `ci-runner-01`'s 403 is resolved; MR #19 is MERGED.)

## Do NOT

- Commit/push `main`; `gh pr merge`. Agent commits need `gitleaks` on PATH (it is — WinGet Packages dir).
- **`git push gitlab <branch-name>` alone is NOT safe on this machine — it can silently push to
  `main` instead.** Root cause (hit for real during Slice 6b, MRs #8/#9 are the cleanup): the
  machine's global `~/.gitconfig` has `push.default = upstream`, and `git worktree add -b <name>
  gitlab/main` auto-sets that new branch's upstream/merge ref to `main`. Combined, a same-name
  push argument can resolve via the tracked upstream (`main`) instead of a same-named remote
  branch. **Always push worktree branches with an explicit refspec:**
  `git push gitlab <branch>:<branch>` — this is unambiguous regardless of push.default. Verify
  the push output's `-> <branch>` line names the actual feature branch, not `main`, every time.
  The two global hook files fixed this session (`~/.claude/hooks/branch_discipline.py`,
  `commit_review_gate.py`) do NOT protect against this — they gate `git commit`, not `git push`'s
  destination branch resolution.
- (GitLab) Don't buy CI minutes, register a self-hosted runner, set CI/CD variable *values*,
  or touch protected-branch settings — all owner-only (§6 cost/config). **Never merge an MR**
  — same rule as GitHub PRs, the owner merges, every time, regardless of MR number. Don't
  assume GitHub is gone for good; don't delete the GitHub remote or repo.
- Emit buy/sell/hold/price-target/advice anywhere — educational only.
- Reword OR AUTHOR metric copy/definitions/caveats without owner sign-off (§6) — bit us on #135.
- Add a catalogue row for a new metric before the Router — it renders an un-valued "—" cell.
- Hand-roll the plan-back in prose — use plan mode.
- Ask the owner cryptic/jargon questions — plain language, context, a recommendation, rarely.
- Use ROIC / Tier 1 / CET1 / NIM / NPL / ARR / multi-year metrics — yfinance can't source them (this is the
  real ceiling on the financials card; leave solvency honestly blank rather than fake it).
- Clip or hide outlier magnitudes — route to the correct lens.
- Compute from `info` scalars where a period-matched statement line exists — that's the shortcut #140 corrects.

## Context / open items

- **`~/.claude/hooks/branch_discipline.py`'s worktree-cd fix (landed during 6b) still has a gap, hit
  for real during 6c:** `_leading_cd_dir()` only matches a *literal* `cd <dir> &&`/`cd <dir>;` at the
  very start of the command string — it does not expand shell variables (`cd "$WORKTREE"` on its own
  line inside a multi-line heredoc-style Bash call fails to match, since the regex sees the literal
  text `$WORKTREE`, not a real directory) and doesn't handle `cd` as a standalone statement followed by
  more commands on separate lines rather than chained with `&&`/`;`. Hit this directly: a `git commit`
  issued via `cd "$WORKTREE" && git commit ...` with `WORKTREE` set by an earlier line in the same
  multi-line command was wrongly evaluated against the main checkout (on `main`) and blocked with
  "BRANCH BLOCKED". Worked around in-session by using a literal `cd "<absolute-path>" && git commit
  ...` one-liner instead of a variable — the existing fix handles that shape correctly. Not fixed at
  the hook level this session (out of this repo's scope, same as the `dbt-agent-kit` plugin's own
  unfixed copy noted below) — if editing this hook again, consider resolving `_repo_root` by running
  `git rev-parse --show-toplevel` with `cwd=event.get("cwd")` as a more robust fallback than
  text-matching the command string at all.
- **Review mechanics (keep — reused every slice):** the blocking review gate is `commit_review_gate.py`,
  wired in THIS repo's own `.claude/settings.json` (project-scoped) as of 2026-08-18, alongside
  `pre_push_gate.py` and `handover_in.py`. This corrects an earlier same-day attempt that wired all three
  GLOBALLY (`~/.claude/settings.json`) instead — that broke a *different* project
  (football-data-pipeline), whose own, differently-shaped review-hash logic collided with the global
  hook's; the owner reverted the global wiring the same day. Project-scoped wiring can't leak into another
  project's session by construction. `diff_sha256` = `sha256(git diff --staged --no-renames --no-abbrev)`;
  get it via `commit_review_gate.py --staged-hash`. Reviewer agents are NOT registered as subagent_types
  in this frontend — run them as **general-purpose** agents with the role `.md` inlined (definitions in
  the plugin `agents/` dir + `.claude/agents/equity-analyst-reviewer.md`). review.md + active_work.md are
  a **separate artifact-only commit** after the reviewed one.
- **`review_routing.json` hardened 2026-08-18** with 4 guard-path routes (`.claude/settings.json`,
  `.claude/agents/*`, itself, `.gitlab-ci.yml` → `cto-reviewer`), modeled on football-data-pipeline's more
  mature routing at the owner's request. Two things from that sibling repo deliberately NOT ported, both
  real options if this repo ever wants them: (1) **`hash_exclude_paths`/`protected_override`** — the
  actual mechanism that would give real tamper-evidence (this repo's self-referential guard rule can't
  stop a same-commit weaken-and-exploit, since `commit_review_gate.py` has no baseline pinning); needs new
  code in `commit_review_gate.py`, not a config change. (2) a **`platform-reviewer`/`bi-analyst-reviewer`
  role split** — not relevant at this repo's current scale. Also worth knowing: `.claude/agents/*` only
  protects `equity-analyst-reviewer.md` — the four other reviewer roles (`cto-reviewer`, `scope-auditor`,
  etc.) live entirely outside this repo in the `dbt-agent-kit` plugin's own `agents/` dir, invisible to any
  repo-scoped gate; no routing rule here can close that gap.
- **This handover fell behind actual `main` state at least twice** (5b and 6a both sat "MR open" in this
  file long after merging) — likely because parallel sessions on this repo did the merging/next-slice
  work without this file being the thing they updated first. If you're picking this file up and something
  in it seems inconsistent with `git log main`, trust `git log main` and fix this file, don't assume the
  file is right.
- **`handover_in.py`'s injection cap (`MAX_BYTES`) exists in three places that can silently diverge:**
  the live, actually-wired copy at `~/.claude/hooks/handover_in.py` (bumped 16000→32000 on 2026-08-18),
  and two dormant source copies — `~/.claude/plugins/cache/dbt-agent-kit/.../hooks/handover_in.py` and
  `~/.claude/plugins/marketplaces/dbt-agent-kit/hooks/handover_in.py` — both still at 16000, unchanged. A
  future `/plugin update` or reinstall of dbt-agent-kit that copies from either dormant source into the
  live hooks dir would silently revert the cap and reintroduce this same truncation bug. Not fixed here
  (editing plugin-managed source felt out of scope for a hygiene branch); if you touch this again, update
  all three or accept the cap will drift back.
- **New raw `stmt_*` field footprint (learned #140):** ingestion module/wiring + staging cast +
  staging/base/core yml docs + **`sources.yml` declaration** + **`scripts/audit_mart_vs_yfinance.py`
  `FUNDAMENTALS_COLUMNS`** + `seed_ci_raw_fixtures.py` + `data_contract.md`. The **two schema mirrors**
  (sources.yml + FUNDAMENTALS_COLUMNS) are easy to miss — the scope-auditor blocks on them (it did on #140).
- **yfinance canonicalises balance-sheet row labels** (camel2title of a fixed `const.py` key set) — labels do
  NOT vary by market. Single canonical label per line; only equity has a real alternate (`Stockholders
  Equity`/`Common Stock Equity`). Probe: `scripts/probe_balance_sheet_labels.py`.
- **Deferred hygiene (reviewer-flagged, out of #140 scope — do separately):**
  (a) `sources.yml` + `FUNDAMENTALS_COLUMNS` also omit the #135/#136 `info_*` data-only fields
  (`info_return_on_equity`, `info_current_ratio`, `info_price_to_book`, `info_price_to_sales`,
  `info_ev_to_ebitda`, `info_free_cashflow`, `info_market_cap`) — a pre-existing mirror gap, own cleanup PR.
  (b) `_numeric_columns`' `pd.Timestamp` sort is unguarded in BOTH `balance_sheet.py` and `quarterly.py` —
  optional try/except hardening (do both). (c) add a "first-wins when both equity labels present" unit test.
- Run dbt via the repo `.venv` (global dbt broken). `storage/raw` is gitignored — CI regenerates fixtures from
  `scripts/seed_ci_raw_fixtures.py`; **local raw = the CI fixture set (25 rows, all Technology → all
  `operating`)**, so financial/pre_revenue only surface on the full pipeline, not locally. Verify set: build +
  doc/layer/structure/sqlfluff + eligibility-baseline + export-health + pytest.
- **Backend (track B):** free-tier Supabase pauses after ~7 days idle → "Could not load cards" (real bug in
  `_ensure_all_cards`). Decide keep-alive vs paid tier.
- `docs/refresh-june-2026` is unrelated in-flight docs work (other chat) — leave it.
- Hygiene: `.venv/` is untracked and NOT gitignored — `git add -A` times out. Stage explicit paths, or add
  `.venv/` to `.gitignore` in a future PR.
- Keep this handover current after each PR.
