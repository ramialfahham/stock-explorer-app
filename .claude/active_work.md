# Active work -- handover

> DISPOSABLE. **Owns:** STATE only -- what is in flight, what is open, and what the next session
> must act on. Rewritten continuously and capped at 32,000 bytes.
> **Never:** a definition, or a narrative of how work went. Those belong in a durable doc, in
> git, or in the MR description. If a rule is only written here, it is lost on the next trim.

_The next session is handed exactly this file. Keep it current. Full history through
2026-09-03 is archived in [`docs/handover_2026-09-03.md`](../docs/handover_2026-09-03.md)
(itself built on [`docs/handover_2026-08-18.md`](../docs/handover_2026-08-18.md);
`docs/handover_2026-05-24.md` deleted in Phase 6, its own stated delete condition long since
true) -- this file stays lean on purpose (it's injected whole at SessionStart by
`handover_in.py`, capped at 32,000 bytes). When a slice/MR merges, collapse its entry here to
one or two lines and let the archive keep the detail._

## In flight

**GitLab issue backlog prioritization push (owner 2026-09-16), IN PROGRESS.** Plan file
`C:\Users\Rami\.claude\plans\vivid-booping-lake.md` (outside this repo) has the full
prioritized sequence across all 15 then-open GitLab issues, reasoned from "what would an
outside reviewer judge first." Work one item at a time, five-step protocol per item, do not
start item N+1 before N is merged.

- **Phase 0, issue #2 (Streamlit Community Cloud migration): CLOSED 2026-09-16.** Verified
  stale -- `render.yaml`/`docs/streamlit_deploy.md` already shipped the Render migration
  this issue asked for (2026-09-14, before this issue's ~1-month-old open date). Live app
  confirmed loading real data at `stock-explorer-app.onrender.com`.
- **Phase 1, issue #3 (ANTHROPIC_API_KEY as Protected CI/CD var): flagged to owner, NOT
  agent work** -- it's a credential value. Until set, the AI-written card read stays
  silently skipped in the scheduled `data-pipeline` job even though the code is merged.
  Not yet confirmed done.
- **Phase 2 item 1, issue #7 (dual-index duplicate cards): MR !171 open, awaiting CI +
  merge.** `frontend/explore_filters.py`'s `filter_pool()` now dedupes by ticker when
  `market_code == ALL_MARKETS`; refactored `dedupe_to_latest_snapshot`'s tie-break logic
  into a shared `_dedupe_by_latest_snapshot(cards, key_fn)` (cto-reviewer round-1 finding).
- **Next action**: once !171 merges, sync `main` and start Phase 2 item 2, issue #4 (three
  small hygiene items -- stale CI-tier doc, `.gitignore` encoding check, `--target dev` for
  `generate_assessments.py`). Then Phase 3 (the centerpiece): issue #20 (persistent search
  on the list), issue #6 (Discover entry ordering -- needs an owner decision on which of 4
  named directions, ask when reached), issue #1 (Slice 6 card redesign, largest item).
  Full remaining sequence (Phase 4 depth features, Phase 5 process/data-quality) is in the
  plan file above -- do not re-derive the priority order, read it.

**Repo-cleanup push (owner 2026-09-15), CLOSED -- all six phases MERGED (!160, !161, !163,
!165, !167, !169).** Detail in each phase's own MR; lasting process lessons folded into
"Context / operational notes" below. Plan file fully executed, nothing outstanding.

**Portfolio-grade push (owner 2026-09-15), CLOSED.** Item 8 (AI-read cost) and MR !116's
guardrail gaps resolved; detail in each MR. **The `--max-reads` value for the
`data-pipeline` CI job is still unset -- owner's call**, ideally after one clean scheduled
run's real counts. Nothing else open from this push.

**Load-time work (owner 2026-09-14: black screen not acceptable, zero spend).** Merged:
!140 header first, splash at first byte, saved list in cookies (owner: A), telemetry off;
!141 `?timing=1` stage clock (keep or remove: owner's call); !142 Streamlit's source watcher
off in production (it scanned every loaded module on the message-flushing thread after each
new session's first run; 3 s here). !143 merged: yfinance (with pandas and numpy) imported only when Saved fetches headlines.
Live after !143, five return visits, script itself 25 ms: first byte 0.2 s (splash), header
2.6 to 2.9 s, full list 2.96 / 3.19 / 3.24 / 3.00 / 3.05 s (this morning: 11.6 s to first
pixel). Cold process (after a deploy or Render's sleep): first visit 15.7 s (was 26 to 44 s),
of which `import app` 9.1 s (was 20 to 33) and the first Supabase deck fetch 5.6 s. What
remains is outside the code: about 2 s of connection and Streamlit session start on Render's
box before our script runs, and the sleep. **NEXT, owner's calls:** a faster free host
(Hugging Face Spaces; the owner must create the Space); reading the deck over plain httpx
instead of the Supabase client library (2.6 s of the import here), a mechanism change.
Owner's to reword: "Loading cards", the splash "Stock Explorer" / "Loading"; keep or remove
`?timing=1`.

**CHECK on the first scheduled run after !129 and !130 (both merged):** (a) `generate_assessments`
summary, `generated=` vs `carried=`, the only measurement of how fast reads converge on the
new labels without a hash bump; (b) `assert_dividend_yield_suspects` WARN count, expected 5.

**Owner question left open by !130:** a decimals-based discriminator for fraction-scale
yields (four decimals = fraction) would catch a fraction row at any yield but mis-scale a
genuine four-decimal percent. Definition territory; not done.


**Issue #9 Tier 1 is closed** with !126 merged (fill floor at 50%, owner-set).

**Three owner questions from the fill floor, none urgent:** (a) CI fixtures are 5 operating,
1 financial, 1 pre-revenue per market, so `dbt build` exercises the floor for operating
metrics only (pytest covers the other types with fixtures); raising the fixture counts widens
`scripts/seed_ci_raw_fixtures.py`. (b) `cash_runway_months` and `burn_rate_monthly` are
legitimately null for a pre-revenue company not burning cash, so a market with five such cards
would trip the floor on correct data; only three pre-revenue companies exist today. (c)
`jinja2` is imported directly in `tests/tooling/test_metric_fill_floor.py` but pinned only
through `dbt-core`; cto suggests an explicit pin in `requirements.txt`.

**Side finding, not root-caused (from the `accepted_range` work, !158):**
`ebit_margin_pct` = 44,944.9% for IAG (au_asx200) -- unlike DYL's already-understood
pre-revenue explosion, this one has no obvious explanation and is worth a look.

**Merged this pass** (detail in each MR): !157 reworks `revenue_growth_yoy_pct`'s catalogue
copy to state verdict-consistent caveats instead of telling readers to discount a decline the
app's own rule treats as real; closes item 2. !155 names the Postgres table explicitly in the
`mart_stock_cards` heading (three reviewers had flagged this in an earlier MR, never fixed
until now). !158 adds `dbt_utils.accepted_range` sanity guards (`severity: warn`) to eight
card metrics prone to near-zero-denominator explosion, bounds measured against production
(detail in `docs/data_contract.md`); closes the `accepted_range` question left open by A2.
!156 closes item 10 (latent `AppTest` crash risk), no action needed. !153 routes
`.claude/working-agreement.md` to
`cto-reviewer` (MR !116's third guardrail gap; the other two declined, not deferred). !151 `--max-reads` caps new Claude calls per run in
the AI-read step (unbounded default, value for CI still unset -- owner's call); clears a
capped/failed card's stale read instead of leaving it under fresh numbers. !149 fixed a live bug where the assessments batch
upsert nulled "carried" cards' `ai_read` whenever a call also held a "generated" record
(root cause of item 8's cost, not just a symptom); also fixed `_fetch_existing_assessments()`
silently capping at 1000 rows. !147 names the sector in a benchmarked metric's own
gloss line ("..., vs sector.") when its range bar is drawn. !145 AI-written read as always-visible bullets
(reversing the earlier card-view fold), "N saved" scoped to the Saved tab only, and the
now-contradicted "first metric above the fold" success check retired. !143 lazy yfinance.
!142 file watcher off in production. !141 timing probe. !140 first paint, cookies, splash.
!118-!139 (excluding intervening handover-collapse MRs, e.g. !121): issue #9 pipeline-audit
closure batch (fundamentals gate, precision caps, mart
grain, market_code test, fill floor, AI-read labels/fold, catalogue wording, dividendYield
scale, playgrounds, CI tiers doc, ROE/working-capital wording, sync_dbt_vars exit status,
financial caveat placement, context ownership headers + byte budgets, generated metric table,
standing rules to durable homes) -- detail in each MR's own contract.md/review.md.

## Atomic card export (MR !115, merged `f98f4025`)

Issue #9 finding A1. The export wrote the deck in batches with no transaction, so a half-failure
served two snapshots mixed. `supabase/migrations/018_atomic_card_export.sql`'s
`replace_cards_snapshot()` replaces the covered `(market_code, snapshot_date)` pairs in one
transaction.

**Owner decisions, ANSWERED 2026-09-09, do not reopen.** (1) `grant delete on
public.mart_stock_cards to service_role` -- granted. (2) The delete can roll a ticker back to an
earlier snapshot, or drop it from the deck when the covered pairs take ALL its rows -- accepted,
over never removing a row, which rebuilds the accumulate-forever growth of open item 1. (3) A
`financial` company-type card (the whole GICS sector, not just banks) whose health block is
withheld loses `FINANCIAL_CAPITAL_ADEQUACY_CAVEAT` -- left as is, filed as issue #11.

**Open, owner's call:** no automated coverage of the SQL function; every test uses a fake
client, and three review rounds found real defects in that surface. Needs a
`services: [postgres]` container in CI.

## What is still wrong (the open record)

**Issue #9, the pipeline audit, is the complete record -- read it before starting cleanup
work.** Its Tier-1 findings are all closed: the mixed-snapshot export (!115), the
`dividendYield` scale guard (!114), price-ingestion reporting (!118), the fundamentals gate
(!122), the precision caps (!123), the mart grain (!124), `market_code` vs folder (!125), the
fill floor (!126), the AI read's labels and rendering (!129). The learn panel's playgrounds
(B1): !132, merged; issue #9 fully closed. Issue #10 (mixed `dividendYield` units): !130, merged. Issue #12
(catalogue "banks" wording): !131, merged.

## Recently merged (detail in each MR's own contract.md / review.md)

- **!114** two-sided percent-scale guard for the three Yahoo passthroughs. The trap worth
  remembering: `dividendYield` arrives as a percent, `revenueGrowth`/`returnOnEquity` as
  fractions x100, so a one-sided bound is blind to two of three. Bands and known holes in
  `docs/data_contract.md`.
- **!111** first-visit deck fetch, 18.38 MB -> 1.46 MB. See Do NOT: it did not fix what the
  owner experiences.
- **!106** deterministic style guard for AI card reads. **!104** first Streamlit `AppTest` e2e
  test. **!103** dbt model contract + source freshness (table-level limitation is open item 9).
  **!101** pipeline alerting, route now live via GitLab per-user notifications
  (`docs/operations_guide.md`). **!100** capital-adequacy caveat.
- **!92** 5-metric benchmark expansion. **Caution for any future benchmark aggregate over a
  ratio whose denominator can flip sign**: the new aggregates had no guard against negative
  stockholders' equity, a class already guarded at the verdict layer but never at aggregation.
- **!116** deleted the narrative prose that caused six of !115's eleven review rounds and put
  the rule in the working agreement §2: prose earns its place only if it records a decision not
  derivable from code, defines something the code cannot state, or is machine-checked. Also
  corrected three instructions in that file that were FALSE, not stale: "stage everything
  (`git add`)", pushing to `origin` with `gh`, and the claim that any merge command is
  hook-blocked.
- **!97** README deploy target + screenshot; GitLab topics/description done.
- **!95-!98** (merged 2026-09-05, after `docs/handover_2026-09-03.md`'s cutoff, so NOT in that
  archive -- detail is in each MR's own `contract.md`/`review.md`): browser-storage coverage,
  Discover/Search nav state loss, README accuracy, Saved-tab confirm + per-item removal. !98's
  planning caught two real bugs first: an out-of-sync "is this saved" check that would have
  stranded a removed ticker, now the shared `saved_keys_with_order()`, and a
  `clear_interactions()`/`st.rerun()` ordering bug.
- **!73-!87** the nine Gemini-feedback points: see `docs/handover_2026-09-03.md`.

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

Live owner decisions a future session must act on, not numbered because they are not defects:

- **Repo goes public once it is portfolio-grade, not before** (owner, 2026-09-08). Sequencing,
  not a standing block: it stays private through the remaining substance work and flips public as
  the last step. Portfolio-grade means the PIPELINE, not presentation -- owner, 2026-09-09: "this
  is not about make-up, it's about substance, specifically the engineering part". Issue #9's
  findings are what that tracks.
- **Link-preview/avatar image: deferred, unresolved.** Cropping the README screenshot chopped
  mid-sentence prose and was illegible at avatar size; three generated icon concepts were
  rejected outright. Revisit only with the owner's own asset or a clearer direction, never by
  generating more variations.

- **Rename one of the two "working agreement" files.** `.claude/working-agreement.md` holds the
  agent process, `docs/working_agreement.md` holds the UX PR gate. They differ only by hyphen
  versus underscore, and a session cited the wrong one for a whole session before noticing. A
  rename touches every reference, so it is its own change.
- **Context-file debt: closed** (the Do NOT rules have durable homes, dead
  `task/contract.md` pointers deleted, dates stripped from code comments). Untouched on
  purpose: dates inside `supabase/migrations/*.sql`, which are applied history.

Numbered defects and gaps:

0. **THREE OWNER DECISIONS RESERVED BY MR !116.** (c) CLOSED 2026-09-15:
   `.claude/working-agreement.md` now routes to `cto-reviewer` in `review_routing.json`
   (project-local, no cross-repo reach). (a) and (b) **DECLINED 2026-09-15, not deferred --
   do not re-raise without new owner instruction.** Both need editing a file OUTSIDE this
   repo shared by every project on the machine (dbt-agent-kit's own `CONTRACT_TEMPLATE.md`/
   `REVIEW_TEMPLATE.md` for (a), `~/.claude/hooks/branch_discipline.py` for (b), which would
   also need to start blocking `glab mr merge` alongside the `gh pr merge` it already blocks).
   Owner's reason: past global-file edits have broken sibling projects before (see Context /
   operational notes below), and that risk isn't worth taking for either gap. The working
   agreement §3 keeps stating (b)'s gap honestly rather than oversell the guard.

   **And three from MR !118, same reason, all data-contract questions (§6):** (d) the price
   counters cannot see a symbol yfinance returns as an all-NaN OHLCV block; closing it needs a
   contract-level rule, and a bare `not_null` on `close` is wrong because legitimate NaN exists.
   (e) Nothing enforces the "nothing reads prices" precondition the no-gate decision rests on;
   a `ref('stg_yf__daily_prices')` would make it wrong silently. (f) A separate CI job with
   `allow_failure: true` would surface price loss as a visible pipeline warning without gating;
   it is a new workflow step and was never put on the menu.

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
   this pattern shows up on more tickers. **Eviction is now REACHABLE, and still undecided:**
   the atomic export (MR !115) deletes the `(market, date)` pairs a payload covers, so a ticker
   leaves the deck when those take ALL its remaining rows. Whether it should evict BY SNAPSHOT
   AGE is still an owner call.
2. **CLOSED 2026-09-15.** The growth metric's card copy told readers "one quarter can be
   noisy, so look for a pattern over time" while the verdict's own growth gate
   (`GROWTH_DECLINE_THRESHOLD_PCT = 0.0`) reacts to any single-quarter decline, no tolerance
   -- a deliberate design the owner already confirmed by rejecting a -5% tolerance on this
   exact argument. Owner decision: reword the catalogue copy (`revenue_growth_yoy_pct`'s
   `interpretation`/`learn` fields) to state the genuine, verdict-consistent caveats
   (selling off part of the business, currency swings, a contract landing in a different
   quarter) instead of telling the reader to discount the signal.
3. **The financial-type card's capital-adequacy caveat: closed.** MR !100 made it a
   deterministic card-face line (`FINANCIAL_CAPITAL_ADEQUACY_CAVEAT`, owner wording); MR !137
   moved it out of the health block so a withheld block no longer drops it (issue #11).
   The wording states only the one invariant fact; "this bank" and "profitability only" were
   both rejected in review as overclaims.
4. **All 4 confirmed bugs from the Discover/Saved/Search UX findings fixed and merged**
   (was `docs/backlog/discover_saved_search_ux_findings.md`, retired by Phase 3 -- its one open
   tail is now issue #14): the stale Search selection resurfacing on an unrelated later query,
   and the Search box / Discover filter both losing their value on tab switch, fixed 2026-09-04
   (root cause: a KEYED Streamlit widget's session_state is evicted too when the widget isn't
   rendered for one script run, not just unkeyed ones as first guessed -- the original doc's own
   candidate fix, a bare `key=` on the Search box, would not have worked; fixed by making both
   widgets unkeyed and managing their durable value as a plain session_state entry instead).
   "Clear saved" had no confirmation/undo, fixed 2026-09-05 (in-place two-click popover swap;
   also added per-item Saved removal, previously impossible).
5. **CLOSED 2026-09-15 by Phase 3.** The 3 backlog docs that were genuinely open
   (`discover_metric_filters_phase2.md`, `name_vs_yfinance_audit_guard.md`, and item 4's Saved
   pagination tail) are retired; their content is now GitLab issues #13, #19, and #14
   respectively, on milestones "1 · Discover depth" / "2 · Data quality".
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
   this table today (`browser_storage.py` only ever touches a browser cookie), so nothing
   is broken yet -- but whoever eventually builds the cross-device sync feature this table is
   reserved for will need to widen the constraint first.
8. **CLOSED 2026-09-15.** `generate_assessments.py`'s AI-read step was the scheduled
   pipeline's dominant, ungoverned runtime cost (~39 of ~65 minutes on the one measured
   9-market run, 2026-09-01). Root cause: a batch-upsert bug was nulling most "carried"
   (should-be-unchanged) cards' `ai_read` every run, so nearly the whole deck looked like it
   needed regeneration regardless of whether `input_hash` actually changed -- fixed, !149. A
   `--max-reads` per-run cap now bounds whatever real cost remains -- !151, value for the
   `data-pipeline` CI job still unset (owner's call, ideally after one clean scheduled run's
   real counts post-!149).

9. **`dbt source freshness` is table-level across all active markets, not per-market**
   (found by data-engineer-reviewer while reviewing the dbt-contract-and-freshness task above,
   2026-09-06). A single market's
   ingestion silently breaking forever would never trip `error_after` as long as other markets
   keep refreshing -- `MAX()` over the union hides it. Documented as a known limitation in
   `docs/data_contract.md`'s Freshness section. Building per-market detection (e.g. a singular
   test grouped by `market_code`) is a new mechanism -- owner's call whether the gap is worth
   closing.
10. **CLOSED 2026-09-15, no further action.** Possible latent crash risk (opening two
    different stock cards' "Understand these numbers" panel in one session) reliably crashed
    under Streamlit's own `AppTest` harness with a `KeyError`, but a manual pass against the
    real dev server never reproduced it; cto-reviewer traced it into Streamlit's own
    `except KeyError: pass` around this exact case, citing upstream issue
    `streamlit/streamlit#7206`. Checked 2026-09-15: that issue is closed and confirmed
    upstream; this repo runs Streamlit 1.57.0, far newer than the 1.25.0 it was reported
    against. Owner decision: close it, no tracked follow-up. Full technical trace in MR
    !104's own `contract.md`/`review.md` if this ever resurfaces.

Sync local `main` before starting anything new if it's drifted behind `gitlab/main`.

## Do NOT

The standing rules live in durable docs now; this is the index. Agent process and decision
rights, including spend nothing and no merge: `.claude/working-agreement.md` §3, §6, §8.
Metric work (statement lines over `info` scalars, no data-layer clipping, the yfinance
ceiling, no fallbacks): `docs/data_contract.md` "Card metrics". A catalogue row carries
`applies_to` from the start: `docs/metric_layer.md` "Adding a metric". Educational only, no
advice: `docs/north_star.md`. The snapshot gate in `attach_assessments` and why it is not
simplified: its docstring in `frontend/explore_filters.py`. Performance, `DECK_COLUMNS` and
why re-measuring the data layer proves nothing: `docs/operations_guide.md` "Performance".
Run `validate:full`'s steps before pushing: `docs/development_workflow.md` "Definition of
done". Reserved and unbuilt from MR !111: a `DISTINCT ON` view to push deck deduplication
into Postgres; `_DECK_TTL_SECONDS`' approved 15-60 minute band sits beside the constant.

## Context / operational notes

- **Review mechanics**: the blocking review gate is `commit_review_gate.py` (global,
  `~/.claude/hooks/`, not tracked in this repo). `diff_sha256` =
  `sha256(git diff --staged --no-renames --no-abbrev -- . ":(exclude).claude/task/review.md")`
  -- `review.md`'s own bytes are excluded from what gets hashed (fixed 2026-09-05; a merge
  commit forces `review.md`'s conflict resolution into the same atomic commit as the
  substantive change, and no hash it holds can describe a diff that includes its own bytes --
  full account in `docs/portfolio-readme-accuracy-fixes`'s MR !97 history). Get the live hash
  via `commit_review_gate.py --staged-hash` -- use it, do not hand-roll the hash; a session
  spent nine review rounds labelling them with `git hash-object` output, which the gate's
  `[0-9a-fA-F]{64}` pattern can never match. The verdict parser needs the literal token
  `VERDICT:` at the START of its own line -- `Round 2 VERDICT: PASS` parses as no verdict at
  all, silently. In a multi-round `review.md`, write earlier rounds as prose and give ONLY the
  final round a bare `VERDICT: PASS`/`FAIL`/`ESCALATE` line. **The `##` section header itself
  must be the literal required-reviewer name** (`## cto-reviewer`, `## scope-auditor` --
  exactly as `review_routing.json` spells it), not a round label -- the gate maps headers to
  reviewer names by exact string match, so a differently-named header reads as "no verdict"
  even with a correct `VERDICT:` line inside it (hit 2026-09-16, issue #7's dedupe fix).
  Reviewer agents are NOT registered as
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
  file touching more than one obvious category. **A file added to scope mid-task can pull in
  a reviewer never dispatched until the commit gate itself blocks on it** (repo-cleanup
  Phase 3: a `*.sql` file added late needed `analytics-engineer-reviewer`, missed until the
  gate caught it) -- re-check the routing against the FULL current staged path list, not just
  the reviewers you started with, whenever scope grows mid-task.
- **A read-only Supabase production query needs explicit owner approval each time** -- the
  auto-mode classifier blocks it by default ("Production Reads"), even a plain
  `SELECT MIN/MAX/COUNT`. `.env` credentials being present doesn't pre-authorize the query
  (repo-cleanup Phase 5, measuring `accepted_range` guard bounds).
- **`handover_in.py`'s injection cap exists in three places that can silently diverge**: the
  live, wired copy at `~/.claude/hooks/handover_in.py` (32000 bytes), and two dormant plugin
  source copies (`~/.claude/plugins/cache/dbt-agent-kit/.../hooks/handover_in.py` and the
  `marketplaces` sibling), both still at the old 16000 value. A future plugin
  update/reinstall from either dormant source would silently revert the cap. Not fixed at
  the plugin-source level (out of this repo's scope); if touching this again, update all
  three or accept the cap will drift back.
- **Global/machine-shared file edits (`~/.claude/hooks/*`, the dbt-agent-kit plugin's own
  files) have broken a sibling project before** -- a global hook change once broke
  `football-data-pipeline`'s review gate. This is why MR !116's (a) and (b) sub-items were
  declined outright (2026-09-15, item 0 above) rather than attempted: the owner's own
  experience is that this category of edit costs more than it's worth. Don't propose one
  without asking first, and expect "no" as the default answer.
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
  (1st/15th, 06:00 UTC) and refreshes production unattended. The GitHub account is permanently
  suspended and its `origin` remote has been deleted from this clone (working agreement §3);
  push to `gitlab`, use `glab`, never `gh`. Full narrative (the account-recovery story, the
  CI-minutes/runner
  consolidation saga, the branch-protection ordering trap) is in
  `docs/handover_2026-08-18.md` and `docs/handover_2026-09-03.md`.
