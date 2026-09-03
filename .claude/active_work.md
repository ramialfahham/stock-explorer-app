# Active work -- handover

_The next session is handed exactly this file. Keep it current. Full history through
2026-09-03 is archived in [`docs/handover_2026-09-03.md`](../docs/handover_2026-09-03.md)
(itself built on [`docs/handover_2026-08-18.md`](../docs/handover_2026-08-18.md) and
[`docs/handover_2026-05-24.md`](../docs/handover_2026-05-24.md)) -- this file stays lean on
purpose (it's injected whole at SessionStart by `handover_in.py`, capped at 32,000 bytes).
When a slice/MR merges, collapse its entry here to one or two lines and let the archive keep
the detail. **Archival pass done 2026-09-03**: this file was ~146KB (the SIZE WARNING first
flagged by scope-auditor on 2026-08-28 at ~95KB was never actioned before this pass); trimmed
back under cap by moving settled history into the new archive above._

## Recent work (2026-09-01 to 2026-09-02)

This session shipped every one of the nine Gemini-feedback points in
[`docs/backlog/gemini_verdict_feedback.md`](../docs/backlog/gemini_verdict_feedback.md) --
that doc now has nothing outstanding. In order:

- **MR !73 -- ratio sign-inversion guard (point 1).** `net_debt_to_ebitda`/`debt_to_equity`
  now band `unknown`/`weak` instead of reading a sign-flipped ratio as good when a
  denominator goes negative.
- **MR !75 -- joint liquidity evaluation (points 6/8).** `current_ratio_stmt` gets relief
  (bands `ok`, never `good`) when free cash flow covers the working-capital shortfall in
  real dollars, not a revenue-scaled margin. Fixes Apple's card reading "Mixed".
- **MR !77 -- statement_roe_pct sign-inversion guard**, sibling bug to !73, same mechanism.
- **MR !79 -- declined sector/size threshold calibration (point 9).** Current fixed
  thresholds already mirror standard financial conventions (credit-quality bands, textbook
  liquidity ratios); sector-relative calibration would let a mediocre company in a weak
  sector read green purely because its peers are worse. **Decision: do not calibrate.**
- **MR !81 -- structured AI-read output + hallucination guard (points 3/4).** Claude Haiku's
  read call forces tool-use; a numeric cross-check (`validate_read_metrics`) rejects any
  cited number that doesn't match the card's own data, fails closed (no retry). Added a
  deterministic one-line fallback ("What the verdict means") for when `ai_read` is absent,
  which previously rendered as a bare badge and read as broken.
- **MR !83 -- dropped a hardcoded-looking example** (a real company's exact figures baked
  into a `docs/data_contract.md` bullet) after the same pattern in a code comment caused
  Claude to misdescribe logic as "hard-coded" to the owner. **Standing rule: no concrete
  real-world examples or version-history narrative in code comments or docs describing
  current behavior -- state the rule and its rationale only.**
- **MR !85 -- declined early-stage classification review (point 2).** 4DMedical's -823.3%
  operating margin is an honest number for a genuinely early operating company, not the same
  degenerate case (Deep Yellow) the 0.1%-of-market-cap `pre_revenue` threshold exists to
  catch. Moving the threshold would be the same invented-number problem point 9 was declined
  for.
- **MR !87 -- outlier-aware metric-range scaling (point 5).** `benchmark_range()` clamps the
  displayed axis to a Tukey fence (`Q1 - 1.5*IQR` .. `Q3 + 1.5*IQR`) instead of raw sector
  min/max, so one extreme peer no longer dominates every other card's marker in the same
  sector; a no-op when no real outlier exists. Needed new dbt-computed quartile columns
  (`sector_q1_*`/`sector_q3_*`) + a Supabase migration, not a frontend-only change. **This
  also resolves the "one ASX Energy stock distorts its whole sector's range mark" data-quality
  issue flagged back in MR #24 (2026-08-30) as a dbt-layer fix, owner call** -- it shipped as
  a display-layer fix instead, which fully addresses the symptom.

Each of these went through the full review-routing cycle (scope-auditor always, plus
cto-reviewer/analytics-engineer-reviewer/equity-analyst-reviewer/data-engineer-reviewer per
path) as cold, blinded `general-purpose` agents reading the role `.md` inlined. Every branch
followed: commit main change, commit `review.md` separately, push to `gitlab` (never
`origin`, which points at a suspended GitHub account), open MR, wait for the owner to merge,
then sync/delete/prune, then a trivial follow-up MR flipping this file's status line (direct
commits to `main` are hook-blocked). Full round-by-round review trails, including three real
FAILs this session (cto-reviewer catching two silent failure branches and a label-uniqueness
gap on !81; scope-auditor catching scope creep on !83's "minimal trim" turning into a
reword; a missing blank line on !85), are in `docs/handover_2026-09-03.md`.

**MR !92 (2026-09-03) -- 5-metric benchmark expansion, merged.** Owner-approved follow-up to
!22, not one of the nine Gemini points above (scoped down from an original "11-metric" idea
after finding pre-revenue's 3-company coverage could never clear the 8-peer rendering
threshold). Extends the range-mark feature from 4 to 9 benchmarked metrics
(`debt_to_equity`/`current_ratio_stmt`/`statement_roe_pct`/`net_margin_pct`/`roa_pct` added).
Mid-review, two reviewers independently caught a real bug: the new
`debt_to_equity`/`statement_roe_pct` sector aggregates had no guard against negative
stockholders' equity, the same sign-inversion class !73/!77 already guard at the verdict
layer but that guard never covered peer-benchmark aggregation. Fixed and escalated to the
owner (approved, "go") since it broke the task's own "no metric-specific exception" scope --
worth reading as a caution for future benchmark-style aggregates over any ratio with a
denominator that can legitimately flip sign. Also caught post-push: a `sqlfluff`
line-length violation CI flagged that should have been checked locally before the first
push -- run `sqlfluff lint dbt_analytics/models dbt_analytics/tests` (and the rest of
`validate:full`'s local-equivalent commands) before pushing, not just `pytest`/`dbt build`.

## Standing decisions (durable -- do not re-litigate without new evidence)

- **Metric-assignment matrix**: perspectives (valuation/profitability/growth/solvency/
  liquidity/cash/returns) are semi-universal lenses; the metric filling each is type-specific;
  some lenses are honestly EMPTY (never fill with a weak proxy). Financial (bank) cards have
  no sound solvency/liquidity/cash metric sourceable from yfinance -- leave it blank.
- **Metric definitions**: statement ROE = common income / common equity; ROA = net income /
  total assets from statements; `cash_runway` = cash / FCF-burn in months. New computed
  columns coexist with info-scalar equivalents, never replace them silently.
- **yfinance `dividendYield` is a PERCENT, not a fraction** (0.94 = 0.94%, verified live).
  `payoutRatio`/`returnOnEquity`/`returnOnAssets` ARE fractions. A future yfinance version
  reverting this would ship a silent 100x error -- there's a persisted scale-regression guard
  for it.
- **Filter every future metric suggestion through**: sourceable from yfinance? legible to a
  true beginner? An external review (Gemini) proposed CET1/Tier1/LCR/NIM/ROIC/ARR/NRR/TAM --
  all rejected as unsourceable and/or too advanced. Only ROA survived both filters.
- **Cataloguing a metric RENDERS it** (catalogue -> metrics.json -> card_copy -> card_ui,
  uniform). A metric can be computed and data-only (no catalogue row) without being shown.
- **Authoring metric copy/caveats, rewording user-visible text, and anything changing an
  already-shipped output/number is a §6 owner call, every time.**
- **AI assessments**: educational, never advice; true-beginner language; reason only from the
  given numbers; end on the health verdict.
- **Growth feeds the verdict one-sidedly**: a shrinking top line blocks green; growth never
  earns green, never causes red (a company can grow into losses). Do NOT make this symmetric.
- **`burn_rate_monthly` stays shown and unread by the verdict**, deliberately: runway already
  divides cash by burn, so reading burn separately double-counts, and a ratio alone destroys
  magnitude information the raw number carries.
- **Currency display**: real-world form per currency, not a uniform rule. CHF renders bare
  (no symbol in general use); CAD -> C$ (follows AUD -> A$); SEK/DKK/NOK stay ISO codes
  ("kr" names three different currencies). Changing this means editing BOTH copies of
  `_CURRENCY_SYMBOLS` (`scripts/assessment_rules.py` and `frontend/card_copy.py`) and NOT
  bumping `INPUT_HASH_VERSION` (a mirror-drift test, `test_currency_symbol_maps_are_mirrors`,
  catches a single-copy edit).
- **Percentile/sector-relative ranking for verdict thresholds is rejected**, twice now (an
  earlier general rejection, then point 9's full investigation): "being in some top
  percentile can still mean an unhealthy state if the whole sector is in an unhealthy state."
  Rating agencies' per-industry ABSOLUTE thresholds would be the legitimate shape to copy if
  this is ever revisited, not relative ranking. **The file used to carry a "Step 3:
  sector-calibrated thresholds, THE next fundamental piece" section proposing exactly this --
  removed in this pass as superseded by point 9's decline; see the archive if the historical
  reasoning is ever needed.**
- **Changelogs live in one place**: code and docs describe the present; git, this file, task
  contracts and review records carry history. Never date-stamp a fix into a comment or doc
  prose describing current behavior.
- **No em/en-dash on any line added to this repo, anywhere, any file** -- flagged repeatedly
  this session; use `--` instead, matching the convention already used throughout this repo's
  own prose.

## Market coverage

Nine markets active (as of the last check, 2026-08-27): US S&P 500, UK FTSE 100, Japan
Nikkei 225, Australia ASX 200, Germany DAX, France CAC 40, Netherlands AEX, Switzerland SMI,
Spain IBEX 35. Six more agreed and queued, not yet onboarded: Finland, Sweden (OMXS 30),
Denmark, Norway (OBX), Canada (TSX 60), Italy (FTSE MIB) -- batched together, each still
getting its own coverage audit. **Read `docs/data_contract.md`'s market activation checklist
before onboarding any of them** (the `onboard-market` skill routes there); it carries the
procedure and two traps no other doc holds (Wikipedia rejecting pandas' default user agent;
`table_index` being positional and silently wrong rather than erroring).

Known, not necessarily still current (pipeline has run repeatedly since these were measured;
re-verify before relying on any of it): the 20-card warn threshold is absolute, not
proportional to constituent count, so Switzerland (20 members) warns unless every single one
is eligible -- **decided 2026-08-28: this is wrong, fix in phase 2, not on any single
onboarding branch.** The coverage audit for France/Netherlands/Switzerland/Spain was only
ever sample-verified, never full-run-verified from this environment. Seed tickers sat at 1079
against a 959-ticker, 73-minute pipeline run and a 2-hour CI timeout, with headroom narrowing
each batch and nobody tracking it as of the last check.

## Open items (carried forward, genuinely unresolved as of 2026-09-03)

1. **BXB, RMS, SPK (`au_asx200`) are still stuck on a 2026-08-20 snapshot as of 2026-09-03**
   (re-verified against live production; the rest of `au_asx200` is on 2026-09-01), 14 days
   and 4+ runs stale. **Root cause found**: `revenue_growth_yoy_pct` (one of the four
   operating-eligibility fields, computed straight from Yahoo's `info.revenueGrowth` scalar
   with no fallback) is `None` for all three in live yfinance data right now, confirmed by
   direct probe, though it had a real value as of the 08-20 snapshot -- a genuine, current
   Yahoo data gap for these specific tickers, not an app bug. **Owner decision 2026-09-03:
   leave it for now** -- known, accepted category of yfinance noise, not worth building a
   revenue-growth fallback (e.g. computed from ingested total-revenue statement rows instead
   of the fragile info scalar) for three cards. Revisit if Yahoo's data doesn't recover, or if
   this pattern shows up on more tickers. **Still separately open, not resolved by the above:
   there is no eviction mechanism** -- a ticker that stops being exported keeps its last card
   in the deck indefinitely (frontend dedupes to newest row per ticker, not newest snapshot).
   Whether the deck should evict by snapshot age remains an owner call.
2. **The growth metric's card copy tension** ("One quarter can be noisy, so look for a
   pattern over time") sits on cards the growth gate can downgrade on exactly one quarter --
   owner's call, not resolved.
3. **The bank card's capital-adequacy blind spot** survives only as an LLM prompt instruction
   with no card-face caveat, so a card with a null `ai_read` warns nobody. Needs new bank-card
   copy (§6, owner content).
4. **`frontend/browser_storage.py` has zero test coverage**, likely because it wraps a
   Streamlit component awkward to test without a live session. Pre-existing gap, not
   introduced by any specific branch.
5. **Full Discover/Saved/Search user-flow simulation done 2026-09-03**, findings logged to
   `docs/backlog/discover_saved_search_ux_findings.md` -- 4 confirmed, reproducible bugs (a
   stale Search selection resurfacing on an unrelated later query; the Search box's typed text
   and Discover's market/sector filter both silently reset on tab switch, two different
   mechanisms, one not yet root-caused; "Clear saved" is one click with no confirmation, no
   undo, and also wipes skip history) plus one unconfirmed structural risk (Saved has no
   pagination, same class of gap MR !70 fixed for Discover, not reproduced as felt lag at the
   17-save volume tested). No fixes chosen yet -- owner decisions needed, see that doc's "Open
   questions."
6. Three of the seven backlog docs in `docs/backlog/` are genuinely open (the other four are
   closed/resolved -- see that directory): `discover_metric_filters_phase2.md` (a prior
   attempt was built and reverted; needs redesign against its own stated revisit criteria),
   `name_vs_yfinance_audit_guard.md` (needs owner decisions on live-fetch vs. cached snapshot,
   fuzzy-match tolerance, market scope, and hard-fail vs. warn-only before it's build-ready),
   and the new `discover_saved_search_ux_findings.md` from item 5 above.
7. **Free-tier Supabase pauses after ~7 days idle** ("Could not load cards", a real bug in
   `_ensure_all_cards`), never resolved -- and the current biweekly pipeline schedule
   (1st/15th) creates gaps up to ~15 days between writes, longer than the pause threshold.
   Worth checking whether this is silently affecting production right now, and deciding
   keep-alive vs. a paid tier.

Sync local `main` before starting anything new if it's drifted behind `gitlab/main`.

## Do NOT

- Commit/push `main`; run `gh pr merge` or merge any MR -- the owner merges, every time,
  regardless of MR number.
- **`git push gitlab <branch-name>` alone is not safe on this machine -- it can silently push
  to `main` instead**, because the global `~/.gitconfig` has `push.default = upstream` and a
  worktree branch's upstream can resolve to `main`. Always push with an explicit refspec
  (`git push gitlab <branch>:<branch>`) and verify the push output's `-> <branch>` line names
  the actual feature branch.
- Buy CI minutes, register a self-hosted runner, set CI/CD variable *values*, or touch
  protected-branch settings on GitLab -- all owner-only (§6 cost/config).
- Emit buy/sell/hold/price-target/advice anywhere -- educational only.
- Reword or author metric copy/definitions/caveats without owner sign-off (§6).
- Add a catalogue row for a new metric before it has a per-type display assignment --
  renders an un-valued cell.
- Hand-roll a plan-back in prose -- use plan mode.
- Ask the owner cryptic/jargon questions -- plain language, context, a recommendation,
  sparingly.
- Use ROIC/Tier 1/CET1/NIM/NPL/ARR/multi-year metrics -- yfinance can't source them; this is
  the real ceiling on the financial-card lens, leave it honestly blank rather than fake it.
- Clip or hide outlier magnitudes at the data layer -- route to the correct lens (the display
  layer now handles visual compression via the Tukey-fence range-mark clamp, MR !87).
- Compute from `info` scalars where a period-matched financial-statement line exists.
- `git add -A` in this repo -- `.venv/` is untracked and NOT gitignored, and adding it times
  the command out. Stage explicit paths.

## Context / operational notes

- **Review mechanics**: the blocking review gate is `commit_review_gate.py`, wired
  project-scoped in this repo's own `.claude/settings.json`. `diff_sha256` =
  `sha256(git diff --staged --no-renames --no-abbrev)`, get it via
  `commit_review_gate.py --staged-hash`. Reviewer agents are NOT registered as subagent_types
  in this frontend -- dispatch them as `general-purpose` agents with the role `.md` inlined
  (roles live in the `dbt-agent-kit` plugin's `agents/` dir, plus
  `.claude/agents/equity-analyst-reviewer.md`, the one role this repo keeps in its own tree).
  `review.md` + this file are a separate, artifact-only commit after the reviewed one.
- **`review_routing.json` routes by staged PATH, not by what the change does** -- and two
  patterns can both match one file (e.g. `*.sql` -> analytics-engineer-reviewer AND
  `supabase/*` -> data-engineer-reviewer both match a Supabase migration file), requiring
  both reviewers. The commit gate catches a missed one; re-check routing carefully for any
  file touching more than one obvious category.
- **`handover_in.py`'s injection cap exists in three places that can silently diverge**: the
  live, wired copy at `~/.claude/hooks/handover_in.py` (32000 bytes), and two dormant plugin
  source copies (`~/.claude/plugins/cache/dbt-agent-kit/.../hooks/handover_in.py` and the
  `marketplaces` sibling), both still at the old 16000 value. A future plugin
  update/reinstall from either dormant source would silently revert the cap. Not fixed at
  the plugin-source level (out of this repo's scope); if touching this again, update all
  three or accept the cap will drift back.
- **This handover has fallen behind actual `main` state before** (entries sitting "MR open"
  long after merging). If something here seems inconsistent with `git log main`, trust
  `git log main` and fix this file, don't assume the file is right.
- **Both `venv/Scripts/dbt.exe` and `.venv/Scripts/dbt.exe` have working local dbt installs
  in this repo (verified 2026-09-03: both parse and build cleanly).** The dbt that IS broken
  is the system-wide one on PATH (a bare `dbt` command resolves outside either venv and
  crashes on `--version`) -- always invoke a project-local venv's `dbt.exe` explicitly, never
  bare `dbt`. Which of the two local venvs to prefer is not itself settled; this session used
  `venv` throughout without confirming `.venv` wouldn't have worked equally well.
  `storage/raw` is gitignored -- CI regenerates fixtures from `scripts/seed_ci_raw_fixtures.py`.
- **Infra (GitHub -> GitLab migration, deploy, Supabase recovery): all DONE, live in
  production.** App is deployed on Render (native GitLab OAuth, auto-deploy on push),
  serving real cards from a new Supabase project (the original is permanently
  GitHub-OAuth-locked and inaccessible). Scheduled `data-pipeline` CI job runs biweekly
  (1st/15th, 06:00 UTC) and refreshes production unattended. `origin` still points at the
  suspended GitHub account -- push to `gitlab`, never `origin`, and use `glab`, never `gh`,
  in this repo. Full narrative (the account-recovery story, the CI-minutes/runner
  consolidation saga, the branch-protection ordering trap) is in
  `docs/handover_2026-08-18.md` and `docs/handover_2026-09-03.md`.
