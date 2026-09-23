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

**Sector-benchmark null-when docs (issue #23), branch `docs/sector-benchmark-null-when-
docs`, review passed, not yet committed/pushed/MR'd.** Re-scoped against #24 (below,
MERGED via !209): rewrote all ~50 `sector_median/min/max/q1/q3_*` descriptions in
`_intermediate.yml`/`_marts.yml` to name each metric's actual null condition against the
corrected gate, replacing the stale blanket "Null when sector_peer_count < 8"; also fixed
`mart_stock_cards.sector_peer_count`'s description (pre_revenue join exclusion is the
dominant cause). Doc-only. **Next: commit, push, open MR.**

**Sector-benchmark per-metric coverage gate (issue #24): MERGED via MR !209.** Found while
scoping #23 above: `int_stock__sector_benchmarks.sql` gated every metric's median/min/max/quantile_cont
on `sector_peer_count >= 8` (peer GROUP size), not on how many of those peers had a
non-null value for that specific metric -- SQL aggregates silently skip nulls, so a
never-gated or wrong-type-gated metric could render off far fewer than 8 real values.
Fix (owner-approved 2026-09-23): each of the 10 metrics gets its own post-filter
`count()`/`n_<metric>` in `sector_medians`; `combined` gates on that, not
`sector_peer_count` (unchanged, still exposed). Full design in
`.claude/task/contract.md`. Reviewer's non-blocking note (now resolved by #23 above): the
~50 column docs said "Null when sector_peer_count < 8," stale against this fix.

**Null-when doc enforcement: MERGED (!207).** Added `check_null_when_documented` to
`check_dbt_documentation.py` (exempts `info_`/`stmt_`/`qtr_` raw passthroughs,
owner-approved); fixed 32 real violations plus 2 pre-existing-but-wrong null claims.
**Durable lesson: a description already containing "null" can still be incomplete -- cost
2 of 4 review rounds.** A larger family (~50 sector-benchmark columns, same gap) deferred
to issue #23, not yet picked up.

**dbt-layer audit + em-dash cleanup: MERGED (!205).** Manual audit vs.
`docs/layering.md`/`docs/engineering_standards.md`: transformation layer clean, no layer
violations, full doc/test coverage. Only real gap (8 files' leftover em/en-dashes,
grandfathered by `check_no_em_dash.py`'s diff-only design) fixed. **Durable lesson: a
"mechanical" rule needing a judgment call IS the owner's -- six review rounds here were the
same root cause, an undocumented exception invented along the way.** Two minor findings
not acted on: `fct_fundamentals_snapshot` is "latest state" not true history despite the
name; staging bypasses `source()` for `raw_parquet_union()` (freshness still works). Third
(`int_stock__sector_benchmarks.sql`'s repetitive CASE blocks, same file the ~50-column
docs gap below tracks) is now covered by issue #23.

**Issue #22 CLOSED.** `verdict_meaning_violation` synonym fix (!202) verified: zero
read-gen failures, backlog cleared.

**Git push auth flakiness:** failed once, retry hung (TaskStop'd), third clean; `glab`'s
token unaffected. If recurring: ask the owner, don't touch the credential store.

**Nav/About redesign + Not-now removal: MERGED (!200).** Overflow menu -> text-labeled
`About` popover; Not-now removed end-to-end; per-row `Remove` added to Saved. **Lesson:
an objective copy DEFECT is a mechanical fix, not an approval round-trip -- only a change
to what the copy CLAIMS needs asking.** Popover alignment (~2.4px gap) accepted as-is.

**Metric-preset filter bug: MERGED (!197).** Two of five presets checked fields
`DECK_COLUMNS` never fetched, silently passing everything -- fixed; `metric_preset_options`
now hides a preset only when its target type(s) have zero eligible cards, data-driven.

**Discover control-tier contrast: MERGED (!198).** Landed on two tonal tiers by FUNCTION:
content (unchanged) vs control (every button/input, one step lighter). **Lesson: when
visual iteration keeps getting rejected as "random," ask what FUNCTIONAL categories the
elements fall into first, don't keep tweaking hex values.**

**GitLab issue backlog prioritization push (owner 2026-09-16), CLOSED -- all 5 phases
merged (!171-!179).** Plan file `C:\Users\Rami\.claude\plans\vivid-booping-lake.md`
(outside this repo). **Lesson: citing past incidents as precedent is not the owner
deciding fresh (working-agreement.md SS7).**

**Repo renamed stock-swipe-app -> stock-explorer-app: MERGED (!194).** GitLab project,
GitHub mirror, local `gitlab` remote, every in-repo reference, and the push-mirror's PAT
all fixed/verified. **Local folder `D:\Projects\stock-swipe-app` still NOT renamed** --
owner will do it after closing a session (renaming a live session's cwd breaks its shell).

**README scope note: MERGED (!193).** Owner's exact wording, verbatim.
**Lesson: when the owner supplies literal wording, use it verbatim** -- an agent-added
parenthetical, even accurate, is still unauthorized owner-reserved copy.

**Issue #3, #21, Search tab removal, seed governance: MERGED (!181-!184).** Issue #22's
first fix landed in !195 (see the current #22 entry above for status -- issue itself still
open). **Durable lesson: when a fix "feels like a hack," the tell is usually real --
pattern-matching free text to infer something the model already knows is the wrong layer;
make it state that structurally instead.**

**GitHub recovered/published (!185-!187): MERGED.** One-way mirror GitLab -> GitHub, both public.

**Search unified into Discover's filtered list (!188, !189): MERGED.** Three narrow
point-fixes for separate search bugs replaced with one concept: `_discover_pool()` picks
search- or filter-matched rows, `_render_discover_tab()` renders either identically.
**Lesson: a THIRD bug on one feature after two narrow fixes means find the shared root
cause, stop patching symptoms.**

**Nav buttons fixed when re-tapping the active tab: MERGED (!191).** `st.segmented_control`
only reports a NEW selection, silently broke Saved's focus too. Fix: plain `st.button()`s,
always fire, one handler; `bottom_nav` session key deleted, `active_page` sole truth.

**Repo-cleanup push (owner 2026-09-15), CLOSED -- all six phases MERGED (!160, !161, !163,
!165, !167, !169).** Detail in each phase's own MR; lessons folded into "Context /
operational notes" below.

**Portfolio-grade push (owner 2026-09-15), CLOSED.** Item 8 (AI-read cost) and MR !116's
guardrail gaps resolved. **`--max-reads` for the `data-pipeline` CI job still unset --
owner's call**, ideally after one clean scheduled run's real counts.

**Load-time work (owner 2026-09-14, zero spend), CLOSED for now.** !140-!143 merged:
first-paint splash, cookie-based saved list, telemetry/file-watcher off, lazy yfinance.
Warm-run server time re-measured: 141ms -- fast, not the bottleneck anymore. **NEXT,
owner's calls:** Hugging Face Spaces migration; httpx deck fetch instead of the Supabase
client library (mechanism change).

**Owner question left open by !130:** a decimals-based discriminator for fraction-scale
yields would catch a fraction row at any yield but mis-scale a genuine four-decimal
percent. Definition territory; not done.


**Issue #9 Tier 1 closed**, !126 merged (fill floor 50%). Three minor owner questions,
none urgent -- detail in !126's own contract.md/review.md if revisited. **Side finding,
not root-caused (!158):** `ebit_margin_pct` = 44,944.9% for IAG (au_asx200), no explanation.

**Merged, issue #9 pipeline-audit closure batch (!118-!158, all fully merged and closed)**:
fundamentals gate, precision caps, mart grain, fill floor, `accepted_range` guards,
AI-read fixes, catalogue wording, dividendYield scale, load-time work, `--max-reads` cap
(CI value still unset), `.claude/working-agreement.md` routed to cto-reviewer. Detail in
each MR's own contract.md/review.md.

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

Known, not necessarily still current (re-verify before relying on any of it): the 20-card
warn threshold is absolute, not proportional to constituent count, so Switzerland (20
members) warns unless every single one is eligible -- **decided 2026-08-28: wrong, fix in
phase 2, not on any single onboarding branch.** France/Netherlands/Switzerland/Spain
coverage was only ever sample-verified, never full-run-verified. Seed-ticker count vs. the
2-hour CI timeout has narrowing headroom, untracked as of the last check.

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

0. **MR !116/!118's reserved decisions: CLOSED.** (c) done. (a),(b),(d),(e),(f) **DECLINED
   2026-09-15, do not re-raise without new owner instruction** -- each needs editing a file
   OUTSIDE this repo shared machine-wide, or a new CI mechanism never put on the menu; owner's
   reason is past global-file edits breaking sibling projects (operational notes). Detail in
   MR !116/!118's own contract.md/review.md.

1. **BXB, RMS, SPK stuck on a stale snapshot**
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
2. **CLOSED 2026-09-15.** Growth metric card copy contradicted the verdict's own
   zero-tolerance growth gate; reworded to state genuine, verdict-consistent caveats
   instead of telling the reader to discount the signal. Detail in that MR's contract.md.
3. **CLOSED.** Financial-card capital-adequacy caveat: deterministic card-face line
   (MR !100), moved out of the health block so a withheld block no longer drops it (MR !137,
   issue #11).
4. **CLOSED.** All 4 Discover/Saved/Search UX bugs fixed (stale Search selection
   resurfacing, Search/filter value loss on tab switch -- root cause: KEYED widgets evict
   too, not just unkeyed; Clear-saved confirmation/undo + per-item removal). Detail in each
   MR's contract.md/review.md.
5. **CLOSED 2026-09-15 by Phase 3.** 3 backlog docs retired; content is now GitLab issues
   #13, #19, #14.
6. **CLOSED 2026-09-08.** Free-tier Supabase idle-pause: two UptimeRobot monitors
   (`docs/operations_guide.md`), one on the Render app, one hitting Supabase directly --
   **the app monitor alone never covered the database**, a plain HTTP GET only returns
   Streamlit's static shell (websocket-driven), not a real page load.
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

- **Can't directly assign `st.session_state[key] = ...` for a KEYED widget already
  rendered earlier in the SAME run** -- raises `StreamlitAPIException: cannot be modified
  after the widget... is instantiated`. Use `.pop(key, None)` instead; the key is absent
  next run, and a widget with its own reseed-when-absent pattern (search box already has
  one) picks the cleared value up correctly. Hit and fixed via `_clear_search()`.
- **A multi-path `git add` fails ATOMICALLY and SILENTLY-for-the-others if ANY one
  pathspec doesn't match** -- e.g. listing a file's OLD path in the same call right after
  `git mv`-ing it away. The whole invocation errors, and the other valid paths in that
  call don't get staged either, while `git status` right after still looks plausible at a
  glance unless read carefully (`M `/`R ` mixed with unstaged ` M`). Caused a real
  round-1 FAIL on the ticker_overrides.csv seed move (two reviewers independently caught
  it) -- every gate that run had only ever seen the empty rename. After `git mv` + a
  multi-path `git add`, re-check `git status --short`: every line must start with a
  non-space status letter.
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
- **Never seed an unkeyed widget's `value=` from a session_state var the widget itself
  writes.** Its identity is a function of `value=`; reseeding that from the widget's own
  prior output (this file's usual cross-tab-eviction survival pattern, e.g.
  `_render_explore_filters`) moves the identity out from under itself after the first edit
  -- every following edit is silently discarded. Confirmed as a REAL bug on a running dev
  server, not an AppTest artifact (issue #20, `_search_query_widget`); AppTest alone missed
  the worst form (clearing to empty) -- always verify a widget fix live, not just via
  tests. Fix: stable `key=`, reseed `st.session_state[key]` only when ABSENT.
- **A metric being non-null on a card is NOT proof it belongs to that card's company_type.**
  dbt computes each metric from whatever statement fields exist, with no `company_type`
  gate -- e.g. `ebit_margin_pct` and `net_margin_pct` are both non-null on most operating
  cards, not just financial ones. Any type-aware logic (metric presets, future filters)
  must branch on `card["company_type"]` directly, never on "is this metric present" as a
  proxy for type (issue #13, cto-reviewer round-1 finding -- silently ANDed two unrelated
  thresholds together before the fix).
- **This Bash tool's terminal display mangles non-ASCII on the way back -- verify via
  raw-byte decode, never trust a printed `é`/`�` as proof of real corruption.** A file read
  with explicit `encoding="utf-8"` can still print `�` even when the bytes are perfectly
  valid UTF-8 (confirmed via raw-byte check, issue #19's yfinance snapshot). Same root
  cause as the em-dash cp1252 note below -- applies to any non-ASCII content, not just diffs.
- **`git add` EVERY file touched before each review round, not just that round's new
  ones** -- a later round's `git add` listing only its own new files can leave an earlier
  round's edit `MM` (staged + unstaged), so reviewers see a stale staged diff missing the
  fix even though the working tree has it. One reviewer correctly FAILed on
  `git diff --cached`; another PASSed reading the live file instead (as instructed) -- a
  real gap between "looks right on disk" and "what's actually being committed." Run
  `git status --short` before each round, confirm every touched file is a single `M`
  (issue #16, round 2/3).
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
  (1st/15th, 06:00 UTC) and refreshes production unattended. **The GitHub account is
  recovered as of 2026-09-18** (was suspended, which is why this repo moved to GitLab in
  the first place) -- GitLab stays canonical by owner choice, GitHub gets a one-way mirror
  the owner sets up (working agreement §3). No `origin` remote here regardless; push to
  `gitlab`, use `glab`, never `gh`. Full narrative (the CI-minutes/runner
  consolidation saga, the branch-protection ordering trap) is in
  `docs/handover_2026-08-18.md` and `docs/handover_2026-09-03.md`.
