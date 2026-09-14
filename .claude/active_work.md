# Active work -- handover

> DISPOSABLE. **Owns:** STATE only -- what is in flight, what is open, and what the next session
> must act on. Rewritten continuously and capped at 32,000 bytes.
> **Never:** a definition, or a narrative of how work went. Those belong in a durable doc, in
> git, or in the MR description. If a rule is only written here, it is lost on the next trim.

_The next session is handed exactly this file. Keep it current. Full history through
2026-09-03 is archived in [`docs/handover_2026-09-03.md`](../docs/handover_2026-09-03.md)
(itself built on [`docs/handover_2026-08-18.md`](../docs/handover_2026-08-18.md) and
[`docs/handover_2026-05-24.md`](../docs/handover_2026-05-24.md)) -- this file stays lean on
purpose (it's injected whole at SessionStart by `handover_in.py`, capped at 32,000 bytes).
When a slice/MR merges, collapse its entry here to one or two lines and let the archive keep
the detail._

## In flight

**MR !145 open (2026-09-14), branch `ux/ai-read-bullets-and-saved-scope`, awaiting owner
review/merge.** Two card-face/UX fixes from a live screenshot: (1) the "What the numbers say ·
AI-written" block no longer folds behind Read more/Show less -- always-visible bullet list,
one sentence per `<li>`, via `card_copy.py`'s new `ai_read_sentences()` and
`card_ui.py`'s `_bullets_html()`. (2) "N saved" is now Saved-tab-only (owner decision,
2026-09-14), dropped from Discover's list header, Discover's back row, and Search entirely.
Both reviewers passed after two rounds (scope-auditor caught a sentence-split regex bug on
abbreviations like "U.S."; cto-reviewer caught a stale function name in
`docs/ui/disclosure_pattern.md`) -- detail in this branch's own `contract.md`/`review.md`.
**Owner decision, 2026-09-14, same session:** "first metric value above the fold" is retired
as a tracked mobile success check (it was already contradicted by the read no longer folding);
`docs/north_star.md`, `docs/working_agreement.md`'s 480px smoke item, `docs/ui/discover_header.md`,
and two stale code-comment citations in `frontend/styles.py`/`frontend/app.py` updated to match.

**Nothing else in flight.** Load-time numbers below are final for this pass.

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

**Doc wording, three reviewers noted, not fixed:** `docs/data_contract.md` "Supabase export --
`mart_stock_cards`" states the Postgres TABLE's three-column grain under a heading that carries
the dbt MODEL's name, now that the model declares two. Add the word "table" there.

**Owner question left open by A2:** `accepted_range` tests on the card metrics. A definitional
bound (values beyond X are nulled on the card) is a metric definition, owner's. A wide sanity
guard at `severity: warn`, backed by the measured production max, is an engineer's proposal the
owner confirms in one line. Neither exists; decide which, or neither.

**Merged this pass** (detail in each MR): !143 lazy yfinance. !142 file watcher off in production. !141 timing probe. !140 first paint, cookies, splash. !139 generated metric table in the data contract.
!138 standing rules to durable homes; net debt /
EBITDA defined once in its catalogue row. !137 caveat under the metrics (#11). !136 `generate_assessments --target dev` (#4).
!135 `sync_dbt_vars` exit status (#8). !134 CI
tiers doc. !133 owner wording for ROE and working capital; playground heading. !132 playgrounds
follow the card face (#9 B1, the audit's last finding). !131 catalogue "banks" wording (#12).
!130 fraction-scale `dividendYield` scaled on read (#10). !129 AI read labels match the card
(#9 B2). !128 card-view fold. !127 mobile type scale. !126 fill floor, 50% (#9). !125
`market_code` vs folder test (#9 C4). !124 mart grain unit test (#9 C3). !123 migration `019`
drops the numeric precision caps (#9 A2). !122 fundamentals failure gate at 5% (#9 A3). !118
price-ingest visibility (#9 A3; owner questions item 0 (d) to (f) below). !119 context
ownership headers. !120 context byte budgets in CI.

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

There are no `accepted_range` tests; the owner question on them is in the In flight section.

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

0. **THREE OWNER DECISIONS RESERVED BY MR !116, moved here because a task `contract.md` is
   rewritten per task and would have lost them.** None is urgent; none is agent-executable.
   (a) `CONTRACT_TEMPLATE.md` and `REVIEW_TEMPLATE.md` live in the dbt-agent-kit plugin and
   still prescribe the `amendments:` category !116 removed here. Editing them changes every
   project using the plugin. (b) The merge guard matches `gh pr merge` only, so `glab mr merge`
   is blocked by nothing; closing it means editing `~/.claude/hooks/branch_discipline.py`, a
   per-machine file every project shares. The working agreement §3 states the gap rather than
   overselling the guard. (c) `.claude/working-agreement.md` has no required reviewer in
   `review_routing.json` beyond `always`, though it governs every agent action here.
   cto-reviewer recommends routing it to itself, since `.claude/settings.json` and `*hooks/*`
   already route there for carrying execution authority; the evidence is !116, whose only
   blocking correctness finding came from the reviewer routing did not require.

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
2. **The growth metric's card copy tension** ("One quarter can be noisy, so look for a
   pattern over time") sits on cards the growth gate can downgrade on exactly one quarter --
   owner's call, not resolved.
3. **The financial-type card's capital-adequacy caveat: closed.** MR !100 made it a
   deterministic card-face line (`FINANCIAL_CAPITAL_ADEQUACY_CAVEAT`, owner wording); MR !137
   moved it out of the health block so a withheld block no longer drops it (issue #11).
   The wording states only the one invariant fact; "this bank" and "profitability only" were
   both rejected in review as overclaims.
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
   this table today (`browser_storage.py` only ever touches a browser cookie), so nothing
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
  final round a bare `VERDICT: PASS`/`FAIL`/`ESCALATE` line. Reviewer agents are NOT registered as
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
  (1st/15th, 06:00 UTC) and refreshes production unattended. The GitHub account is permanently
  suspended and its `origin` remote has been deleted from this clone (working agreement §3);
  push to `gitlab`, use `glab`, never `gh`. Full narrative (the account-recovery story, the
  CI-minutes/runner
  consolidation saga, the branch-protection ordering trap) is in
  `docs/handover_2026-08-18.md` and `docs/handover_2026-09-03.md`.
