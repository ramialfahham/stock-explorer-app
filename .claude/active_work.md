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

## Recent work (2026-09-09)

**MR !115 OPEN, awaiting owner merge** (`fix/atomic-card-export`) -- issue #9 finding A1. Batched, untransacted
upserts could leave production serving two snapshots mixed. Replaced by
`supabase/migrations/018_atomic_card_export.sql`'s `replace_cards_snapshot()`: one transaction,
delete-then-insert scoped to the `(market_code, snapshot_date)` pairs the payload carries.

**The recurring failure in every review round on this branch, in one line:** asserted, then
"verified" against a fixture that could not disprove it. It produced a single-snapshot guard
built on a false invariant (the mart is multi-date; `fct_fundamentals_snapshot` keeps the
latest row PER TICKER), a `pg_attribute` column list that turned a fail-loud coupling
fail-silent, and four `attach_assessments` unit tests left passing vacuously. Full detail in
`.claude/task/contract.md`'s `amendments:`, which ships with the branch.

**Measured, so nobody re-derives it:** payload 3.9 MB (~6 MB with six more markets) vs an API
accepting 16 MB+; execution 2.87s, 4.21s at double size. `authenticator` carries
`statement_timeout=8s`, `service_role` none; whether 8s binds a service-role request is UNTESTED
(the function is not REST-reachable). If it binds, headroom is under 2x at double scale.

**Owner decisions, ANSWERED 2026-09-09, do not reopen. THREE, not two.** (1) `grant delete on
public.mart_stock_cards to service_role` -- granted. (2) The delete can roll a ticker back to an
earlier snapshot when the payload covers its newest one (older numbers), OR drop it from the
deck when the covered pairs take ALL its rows -- accepted, over never removing a row, which
rebuilds the accumulate-forever growth of open item 1.
(3) A `financial` company-type card (the whole GICS Financial Services sector, NOT just banks)
whose health block is withheld loses `FINANCIAL_CAPITAL_ADEQUACY_CAVEAT`, the line saying ROE
and net margin do not show whether it holds enough capital -- LEFT AS IS and
filed as issue #11, over moving the caveat out of the block, which is card composition and
would put this branch through the UX PR gate.

**Do not "simplify" the snapshot gate in `attach_assessments`.** It is the answer to the
owner's "the user must not be confused": a rolled-back card kept the verdict computed from the
snapshot it is no longer showing, because `card_assessments` is `unique (market_code, ticker)`
and `generate_assessments.py` never deletes. The verdict and AI read are now withheld unless
the assessment's `snapshot_date` matches the card's, compared through `_snapshot_sort_key` (a
bare `str()` would blank every badge app-wide and silently if the column ever gained a time
component). Mutation-verified in both directions. It self-heals next healthy run except for a
ticker out of the dbt mart still holding older Supabase rows: it keeps showing a card whose
assessment is never rewritten. A fully evicted ticker shows no card, so nothing to withhold.

**Still open, owner's call:** NO automated coverage of the SQL function -- every test uses a
fake client, and three review rounds found real defects in it. Closing it needs a
`services: [postgres]` container in CI.

## Recent work (2026-09-08)

**Pipeline engineering audit -- filed as issue #9, findings posted as a comment there.** Three
parallel passes (dbt, export boundary, ingestion+frontend) against the repo's own standards.
Headline: the dbt project and ingestion are genuinely good; almost every real defect sits where
no CI gate reaches -- the export boundary, the frontend, and prose-only standards. **Read the
issue before starting any cleanup work**; it is the only complete record.

Four findings can produce wrong data or a failed run; the first is FIXED on the 2026-09-09
branch above. A half-failed export silently mixed two snapshots; a Yahoo
outlier overflows one of six undocumented `numeric(10,4)` caps (four more columns are
`numeric(18,6)`) and now aborts the whole export transaction (one 500-row batch before); price
ingestion failures print a warning and vanish, so freshness reads green while a third of the
universe lost prices; and the `dividendYield` scale guard did not exist. The last is fixed
below. Also open: the learn panel re-implements four metric formulas in Python against a stated
invariant, and the AI read and the card face disagree on labels and units.

**MR !114, merged** -- two-sided percent-scale guard for the three Yahoo passthroughs
(`assert_percent_scale_passthroughs.sql`), per market, mutation-verified in both directions.
**The trap worth remembering**: `dividendYield` arrives as a percent so a flip makes it 100x
SMALLER, while `revenueGrowth` and `returnOnEquity` arrive as fractions and are x100, so a flip
makes them LARGER. A one-sided floor was blind to two of three. Bands and known holes in
`docs/data_contract.md`'s "Percent-scale passthrough guard".

**Issue #10, filed, not fixed**: production holds `dividendYield` in MIXED units right now --
AvalonBay (0.0387) and Equity Residential (0.0426) are REITs yielding ~4%, i.e. fraction-scale
rows in a percent-scale column. This qualifies the repo's recorded "dividendYield is a PERCENT"
decision to "usually". Nothing user-visible is wrong (the field is data-only) and a per-market
median guard structurally cannot see per-row mixed units.

**Still unguarded, same class:** nothing asserts a fill rate anywhere, so a provider DROPPING a
field (likelier than changing its units) passes every guard silently. The project has no
`accepted_range` tests at all.


**MR !111, merged** -- first-visit load time. Cut the deck fetch from 18.38 MB / 7 round trips
to 1.46 MB / 6. Real, but **it did NOT fix what the owner experiences**, measured live
2026-09-09: TTFB is 210ms, yet a warm session takes ~7.4s to render and a cold one far longer.
The dominant cost is Streamlit's OWN front end -- 54 JS files plus 2 fonts, ~1.2 MB, the last
request finishing around 20s, with 38 KB files taking seconds each on a starved free-tier
instance. No change in this repo's code moves that. The realistic options are a paid Render
plan or not Streamlit (issue #2), both owner calls. **Do not re-measure the data layer and
conclude the app is fast**; measure first paint in a browser.

**Read before touching the frontend fetch path**: `DECK_COLUMNS` is the cold path's entire
cost. Adding a column there is paid by every visitor; adding one to the card face is paid by
nobody until that card is opened. Still unmade: the reserved `DISTINCT ON` view, and the
30-minute `_DECK_TTL_SECONDS` inside the plan's approved 15-60 min band.

**Mobile type scale is too small and unfixed** (owner, 2026-09-09: "completely crap"). Measured
at 375px: 101 of 123 text elements under 14px, body copy 11.5px, labels 10.9px. The tokens are
centralised in `frontend/styles.py` (`--ss-caption-size` 0.72rem, `--ss-label` 0.75rem,
`--ss-row-title` 0.85rem). Changing them is a UX PR gate change (`docs/working_agreement.md`),
needing the 480px checklist.

**MR !106, merged** -- deterministic style/rule guard for AI-generated card reads
(`find_read_style_violations()`, `scripts/assessment_rules.py`), zero new Claude spend. Took
four cto-reviewer rounds, each catching a real bug in the previous round's own fix. Detail in
that MR's `contract.md`/`review.md`.

## Recent work (2026-09-06 to 2026-09-07)

All merged; detail lives in each MR's own `contract.md`/`review.md`. **!104** repo's first
Streamlit `AppTest` end-to-end test (`tests/frontend/test_app_e2e.py`); review caught two wrong
claims of mine, the second became open item 10. **!100** financial-card capital-adequacy caveat.
**!101** scheduled-pipeline alerting + same-day ingestion checkpoint; the alerting route it
documented did not work and sat unchecked until 2026-09-08, now live via GitLab's per-user
notifications (bell -> Custom -> Failed pipeline), see `docs/operations_guide.md`. **!103** dbt
model contract on `mart_stock_cards` + `dbt source freshness` on all three raw sources; its
table-level-not-per-market freshness limitation became open item 9.

**Gotcha for future sessions**: `commit_review_gate.py`'s verdict parser needs the literal token
`VERDICT:` at the start of its own line -- `Round 2 VERDICT: PASS` parses as no verdict at all,
silently. Multi-round `review.md`: earlier rounds as prose, only the final round's verdict as a
bare `VERDICT: PASS`/`FAIL`/`ESCALATE` line.

**Finding, still open (owner's call):** the 2026-09-01 job trace showed ingestion is only ~24 of
the ~65-minute total. The dominant, ungoverned cost is `generate_assessments.py`'s AI-read step
(~39 min, one Haiku call per changed card, no cap). Open item 8 below.

## Recent work (2026-09-01 to 2026-09-02)

All nine Gemini-feedback points shipped (MRs !73-!87; !79 and !85 declined on the owner's
call). Full account in `docs/handover_2026-09-03.md`.

**MR !92, merged** -- 5-metric benchmark expansion (range marks from 4 to 9 benchmarked
metrics). Two reviewers independently caught a real bug mid-review: the new
`debt_to_equity`/`statement_roe_pct` sector aggregates had no guard against negative
stockholders' equity, the sign-inversion class !73/!77 already guard at the verdict layer but
never covered peer-benchmark aggregation. **Caution for any future benchmark aggregate over a
ratio whose denominator can flip sign.** Also: a `sqlfluff` line-length violation reached CI
that a local run would have caught, so run `sqlfluff lint dbt_analytics/models
dbt_analytics/tests` and the rest of `validate:full` locally before pushing, not just pytest.

**Portfolio-readiness: presentation fixes merged, SUBSTANCE is the open half.** MR !97 (README
deploy target, refreshed screenshot) and GitLab topics/description are done. The owner's
correction on 2026-09-09 is the part that matters: "this is not about make-up, it's about
substance, specifically the engineering part" -- portfolio-grade means the pipeline itself,
which is what issue #9's audit findings track.

**Link-preview/avatar image -- deferred, unresolved.** Cropping the README screenshot to a
square chopped mid-sentence prose and was illegible at avatar size; three AI-generated icon
concepts in the app palette were rejected outright ("all 3 are crap"). Revisit only with the
owner's own asset or a clearer direction, not by generating more variations.

**Owner decision on repo visibility (2026-09-08): go public once the repo is portfolio-grade,
not before.** Sequencing, not a standing block -- the repo stays private through the remaining
polish work (topics/description/link-preview image, and whatever else "portfolio-grade" turns
out to need) and flips public as the last step, not a precondition to start on the rest. Don't
treat visibility as something to decide independently of that polish work finishing.

MRs !95, !96, !97 and !98 all merged 2026-09-05 (browser-storage coverage, Discover/Search nav
state loss, README accuracy, Saved-tab confirm + per-item removal). !98's planning caught two
real bugs first: an out-of-sync "is this saved" check that would have stranded a removed ticker
(now the shared `saved_keys_with_order()`), and a `clear_interactions()`/`st.rerun()` ordering
bug. Detail in each MR's own `contract.md`/`review.md`.

## Standing decisions (durable -- do not re-litigate without new evidence)

- **Metric-assignment matrix**: perspectives (valuation/profitability/growth/solvency/
  liquidity/cash/returns) are semi-universal lenses; the metric filling each is type-specific;
  some lenses are honestly EMPTY (never fill with a weak proxy). `financial` company-type cards
  (the whole GICS sector, not just banks) have
  no sound solvency/liquidity/cash metric sourceable from yfinance -- leave it blank.
- **Metric definitions**: statement ROE = common income / common equity; ROA = net income /
  total assets from statements; `cash_runway` = cash / FCF-burn in months. New computed
  columns coexist with info-scalar equivalents, never replace them silently.
- **yfinance `dividendYield` is USUALLY a percent, not a fraction** (0.94 = 0.94%).
  `payoutRatio`/`returnOnEquity`/`returnOnAssets` ARE fractions. This entry used to say
  "is a PERCENT ... verified live" flatly; that is qualified as of 2026-09-08, because
  production holds fraction-scale rows too (AvalonBay 0.0387, Equity Residential 0.0426, both
  REITs yielding ~4%). Issue #10. A wholesale revert would ship a silent 100x error and IS
  guarded (`assert_percent_scale_passthroughs.sql`, two-sided, per market); per-row mixed units
  are NOT, and a median-based guard structurally cannot see them.
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
- **Repo hosting: GitLab-only while the GitHub account (`origin`) remains suspended.** Owner
  confirmed 2026-09-04, explicitly conditional -- revisit only if that account is recovered, not
  something to re-ask otherwise.

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
   this pattern shows up on more tickers. **Eviction is now REACHABLE, and still undecided:** the atomic
   export (branch above) deletes the `(market, date)` pairs a payload covers, so a ticker
   leaves the deck when those take ALL its remaining rows. Whether it should evict BY SNAPSHOT
   AGE is still an owner call.
2. **The growth metric's card copy tension** ("One quarter can be noisy, so look for a
   pattern over time") sits on cards the growth gate can downgrade on exactly one quarter --
   owner's call, not resolved.
3. **The financial-type card's capital-adequacy blind spot, fixed and merged (MR !100).**
   Previously survived only
   as an LLM prompt instruction with no card-face caveat, so a card with a null `ai_read`
   warned nobody. Fixed with a deterministic, owner-approved caveat ("These numbers do not
   show whether this company holds enough capital to stay safe.") that shows on a
   financial-type card in every `ai_read` state, since the prompt only asks the model to
   mention the limit, never guarantees it does (`frontend/card_copy.py`'s
   `FINANCIAL_CAPITAL_ADEQUACY_CAVEAT`, rendered by `frontend/card_ui.py`). It renders inside
   the health block, so a card whose block is withheld loses it too -- see the third owner
   answer above, and issue #11. Two review rounds
   caught the wording overclaiming what it excludes ("this bank" -- `company_type ==
   "financial"` is the whole GICS Financial Services sector, not banks; "profitability only" /
   "profitability and returns only" -- the card also shows a growth metric) before landing on
   this final form, which states only the one invariant fact rather than enumerating card
   contents that can drift independently of this string.
4. **All 4 confirmed bugs from the Discover/Saved/Search UX findings fixed and merged**
   (`docs/backlog/discover_saved_search_ux_findings.md`): the stale Search selection
   resurfacing on an unrelated later query, and the Search box / Discover filter both losing
   their value on tab switch, fixed 2026-09-04 (root cause: a KEYED Streamlit widget's
   session_state is evicted too when the widget isn't rendered for one script run, not just
   unkeyed ones as first guessed -- the original doc's own candidate fix, a bare `key=` on the
   Search box, would not have worked; fixed by making both widgets unkeyed and managing their
   durable value as a plain session_state entry instead). "Clear saved" had no
   confirmation/undo, fixed 2026-09-05 (in-place two-click popover swap; also added per-item
   Saved removal, previously impossible). One item from that doc remains genuinely open, an
   owner product call: Saved has no pagination (unconfirmed as a felt problem at today's
   typical save counts).
5. Three of the seven backlog docs in `docs/backlog/` are genuinely open (the other four are
   closed/resolved -- see that directory): `discover_metric_filters_phase2.md` (a prior
   attempt was built and reverted; needs redesign against its own stated revisit criteria),
   `name_vs_yfinance_audit_guard.md` (needs owner decisions on live-fetch vs. cached snapshot,
   fuzzy-match tolerance, market scope, and hard-fail vs. warn-only before it's build-ready),
   and the new `discover_saved_search_ux_findings.md` from item 4 above.
6. **Free-tier Supabase idle-pause: CLOSED 2026-09-08.** Two UptimeRobot monitors now exist,
   documented in `docs/operations_guide.md`: one on `stock-explorer-app.onrender.com` (Render
   sleeps the web service after ~15 min idle) and one hitting the Supabase REST API directly
   (the project pauses after ~7 days with no activity). **The app monitor alone never covered
   the database**, which is the trap worth remembering: a plain HTTP request to a Streamlit
   app returns only the static shell, because Streamlit runs the app script on websocket
   connect, not on GET. Verified by response body, which contains no card data. Until the
   second monitor was added the database was uncovered and only survived on real visits.
   **Closed on the setup being in place, not on observed effect** -- the database monitor
   cannot be seen working for ~7 days. `docs/operations_guide.md` records how to verify it.
   The app monitor's interval is recorded there (5 min); the database monitor's configured
   interval was not captured, only the requirement that it be well under 7 days.
7. **`supabase/migrations/001_initial_schema.sql`'s `user_interactions.action` CHECK
   constraint only allows `('save', 'skip')`**, stale as of 2026-09-05 against the app-level
   introduction of a third action, `'unsave'` (per-item Saved removal). No live path writes to
   this table today (`browser_storage.py` only ever touches browser localStorage), so nothing
   is broken yet -- but whoever eventually builds the cross-device sync feature this table is
   reserved for will need to widen the constraint first.
8. **`generate_assessments.py`'s AI-read step is the scheduled pipeline's actual dominant,
   ungoverned runtime cost** (~39 of ~65 minutes on the one measured 9-market run, 2026-09-01 --
   found while working item 2, not folded into it, owner's call). One Claude Haiku call per
   eligible card whose inputs changed, no cap. `run_ingestion.py`'s own share of the same run
   was only ~24 minutes (37%) and now has a same-day skip-if-fresh checkpoint (see Recent work
   above) -- this step doesn't, and is the more likely long-term driver toward the 2h CI
   timeout as more markets are onboarded. Not designed here: needs its own look (a time budget,
   a per-run cap, or similar) if/when it becomes the actual constraint.

9. **`dbt source freshness` is table-level across all active markets, not per-market**
   (found by data-engineer-reviewer while reviewing the dbt-contract-and-freshness task above,
   2026-09-06). A single market's
   ingestion silently breaking forever would never trip `error_after` as long as other markets
   keep refreshing -- `MAX()` over the union hides it. Documented as a known limitation in
   `docs/data_contract.md`'s Freshness section. Building per-market detection (e.g. a singular
   test grouped by `market_code`) is a new mechanism -- owner's call whether the gap is worth
   closing.
10. **Possible latent crash risk in a normal, everyday flow: opening two different stock
    cards' "Understand these numbers" panel in one session** (found while building item 4's
    AppTest coverage, 2026-09-07, MR !104). Reliably crashes under Streamlit's own `AppTest`
    harness with a `KeyError` on the next script rerun; a single manual pass against the real
    dev server did NOT reproduce a user-visible crash. cto-reviewer traced the crashing code
    path (`session_state.py`'s `_compact_state`, called via `on_script_will_rerun` inside
    `ScriptRunner._run_script`) into real, shared production code, which wraps this exact case
    in `except KeyError: pass` citing a known upstream Streamlit issue (`streamlit/issues/7206`)
    -- consistent with, but not proof of, one-off manual testing simply not having hit whatever
    narrower condition still lets it through in a real session. Full technical trace in MR
    !104's own `contract.md`/`review.md`. Owner's call: worth a tracked follow-up issue (e.g. a
    few real, repeated manual passes; or reading the upstream issue for whether it's fully
    closed) or leave as-is given production wasn't observed to crash.

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

- **Review mechanics**: the blocking review gate is `commit_review_gate.py` (global,
  `~/.claude/hooks/`, not tracked in this repo). `diff_sha256` =
  `sha256(git diff --staged --no-renames --no-abbrev -- . ":(exclude).claude/task/review.md")`
  -- `review.md`'s own bytes are excluded from what gets hashed (fixed 2026-09-05; a merge
  commit forces `review.md`'s conflict resolution into the same atomic commit as the
  substantive change, and no hash it holds can describe a diff that includes its own bytes --
  full account in `docs/portfolio-readme-accuracy-fixes`'s MR !97 history). Get the live hash
  via `commit_review_gate.py --staged-hash`. Reviewer agents are NOT registered as
  subagent_types in this frontend -- dispatch them as `general-purpose` agents with the role
  `.md` inlined (roles live in the `dbt-agent-kit` plugin's `agents/` dir, plus
  `.claude/agents/equity-analyst-reviewer.md`, the one role this repo keeps in its own tree).
  `review.md` + this file are STILL conventionally committed separately from the reviewed
  change (keeps `git log` readable, one commit per concern), but this is no longer load-bearing
  now that `review.md` is hash-excluded -- committing it alongside the change it describes
  works fine too, and happens by accident sometimes (e.g. when `review.md` is staged to update
  its hash and never unstaged before committing). Not worth guarding against.
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
