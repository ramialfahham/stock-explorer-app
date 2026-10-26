# Active work -- handover

> DISPOSABLE. **Owns:** STATE only -- what is in flight, what is open, and what the next session
> must act on. Rewritten continuously and capped at 32,000 bytes.
> **Never:** a definition, or a narrative of how work went. Those belong in a durable doc, in
> git, or in the MR description. If a rule is only written here, it is lost on the next trim.

_The next session is handed exactly this file. Keep it current. Older history is in git
(the handover archives were removed from `docs/`; `git log --all -- 'docs/handover_*'` finds
them) -- this file stays lean on purpose (it's injected whole at SessionStart by
`handover_in.py`, capped at 32,000 bytes). When a slice/MR merges, collapse its entry here to
one or two lines and let git and the MR keep the detail._

## In flight

**Start here (2026-10-25).** Merged: the small-fix list #44-#47, #53, #54 (!234-!249); the AI-read
changes !251, !252, !257 (catalogue-grounded read, figure and wording checks, 5a.5) and !258 (the
rules' own reasons for the verdict, 5a.6); #48 (!254); #49 (!256); #55 (!264);
#52 items 16, 17, 19 (!265); #51 items 2 to 5
(!266); #71 items 1 to 6 and #43 (!267); #73 (!270: `test_schema_copies_agree.py` also checks the data contract
column table; follow-ups in #78). Criteria
`docs/quality_criteria.json` is v3 (the FE-1 exception is the owner's answer A; DBT-3 allows a
documented raw-file check model). Open follow-ups: #56 (preset cutoffs vs verdict bands), #57
(`importance_tier`, `basis_column`: no production reader), #58 (company identity), #59 (the
scalar-subquery rule cannot fire on a WITH-first model), #60 (owner call: dormant routing
patterns vs GRD-3; recommended: amend the criterion), #61 (real `YFRateLimitError` in the retry
test), #62 (SQL-structure gate and a CTE that mixes a ref with other work), #63 (owner call: may
an import CTE filter?), #64 (`layering.md` says base unions; no base model does), #65 (verdict:
growth plays a small role; researched, the owner chose no new rule; open for a later one), #66
(residual AI-read guard gaps), #67 (prompt-wording items for the owner), #68 (history sentences without a Slice
label in `frontend/styles.py`), #69 (test the atomic export guarantees on a real Postgres in CI: try step 1
first, then the owner decides the cost), #70 (raw-file edge cases from the #51 review). #50 (repo hygiene) is merged; its
unfiled follow-ups are in `.claude/task/review.md` at commit 276b045 (the health gate relies on the dbt
unique test; `PyYAML` pinned in two places; the 3-line `sys.path` block copied in 17 scripts;
`load_markets` error messages; the active-code set built inline in four scripts and two tests): the owner
says which to file. Merged: #72 (!268 the gitleaks launcher, !269 `dim_stock` keeps only the display name, the Used-by
line is required and checked, the grain lines say "each at its latest snapshot_date"; follow-up, not filed: one helper for the
path-to-layer line in `check_dbt_documentation.py`); #74 (!271: search rows keep the lead metric, an empty search
shows `st.info`, dead `saved_count` dropped); #75 (!272: no "More metrics" claim, no Phase B or News row; follow-up
#79). #51 item 6 stays by the owner's answer A; the reworded ING-1 ("no torn file; partial coverage only while a resumable
run is unfinished") goes into criteria v4 below.

**AI read: regenerated on the live data (2026-10-12 to 15).** `INPUT_HASH_VERSION` 5a.6 (!261: revised prompt,
30-word check, one retry inside `--max-reads`). Live result in Supabase: 1222 of 1252 cards have AI text,
30 showed the plain fallback line (refused twice or malformed); the scheduled run of 2026-10-15 (pipeline
2949504220) left 14 of 1252 plain. Scan of the 1222 texts: 0 fractions in words, 0 dashes, 0 "sales" on financial cards, no
closing verdict sentences; **19% say a company "can use ... freely" about free cash flow and 6% predict
("may struggle to pay"); no check catches either (#66, #67; the wording is the owner's call).** The run on
pipeline 2937439062 ran out of Anthropic credit at 08:10 UTC (310 failed calls, 364 blank cards); the rerun
(pipeline 2937731363) generated 334, carried 881, failed 29, used 79 of 128 retries. The live job log shows
only stderr (refusals, failed calls); stdout is buffered until the job ends. Open: #66 (abort the job on a
billing error, flush the log, sector medians in the read need their own check, audit the catalogue text
against ISO/IEC 11179-4, `card_copy.metric_gloss` calls a negative debt ratio net cash even when EBITDA is
negative), #67 (the prompt's example contradicts its own rule; the "freely" and capability wording). The owner's writing
standards (ISO 24495-1, ISO/IEC 11179-4, ASD-STE100) are in
`football-data-pipeline/docs/working_agreement.md` section 9.

**Next, milestone "3 · Professional baseline".** The audit re-run of 2026-10-22 (criteria v3) found 21 defects,
filed as #71 ingestion (done), #72 dbt (done), #73 export (done), #74 frontend (done), #75 docs (done), #76 hygiene (in review); each issue
lists its owner calls apart. **Done = all 21 fixed, then one audit re-run with zero defects** (the owner approves its cost, about 1.7M
tokens: the `quality-baseline-audit` workflow, then `python scripts/verify_quality_audit.py <workflow output JSON>
--report <file>`). Take the issues one at a time, owner decisions one at a time. Criteria:
`docs/quality_criteria.json` v3 (a change needs a version bump and the owner). Way of working the owner set: one rule over every case instead of per-case fixes;
make a sweep's "done" checkable (an exact search and a keep list in the contract); fix every
copy of a changed claim.

**Owner decisions open (ask one at a time):** `scripts/apply_supabase_migrations.py` reads
`GITHUB_ACTIONS` (a Management-API pooler lookup and a "GitHub secret" hint that never run on
GitLab): delete the branch, or port it to `GITLAB_CI`; left alone in #50 because it applies the
Supabase migrations; the refresh
overlap check passes a larger table that contains the whole seed (file an issue or drop);
criteria v4, as DOC-2 and HYG-4 also cite the global `~/.claude/CLAUDE.md`, DOC-2/DOC-5
still name the removed handover archives, and ING-1 needs the reworded rule above; should `verify_quality_audit.py` name NOT AUDITED
areas on the console and exit non-zero; #58's two calls (a home-market rule for the tie-break,
`business_summary` in the deck fetch); a Hugging Face Spaces migration; an httpx deck fetch instead
of the Supabase client library (a mechanism change); whether to add a check that ties the AI read's text to the
verdict (the figure check rejects a read with a sentence that cites no figure).

**This machine:** Smart App Control is on and blocks unsigned `.exe` files (`WinError 4551`): a remote-repo
hook needs `entry: python -m ...` (`test_precommit_config.py`), and the secret scan runs the official gitleaks
through `scripts/run_gitleaks.py` (!268; cached in `.cache/`). The local `.env` has no `SUPABASE_ANON_KEY` and listing `.env`
is blocked by permissions; a read-only production query needs the owner to supply the key.

**Declined by the owner:** revenue-growth fallback, incremental dbt models. Hard constraint:
zero cost. Open from merged work: #29 (review gate bypass spellings), #31 (equity reviewer
FAIL grounds); README demo: disable `gif_creator` overlays.

**Production run, owner-triggered 2026-10-11 (pipeline 2935437069, success, 43 min), the first
with the six new markets, the raw archive, the class-share fix and the facts-only AI read.**
Eligible cards: fi 24, se 30, dk 25, no 24, ca 59, it 40, ch 20 (at the warn line); 1241 in
total. Raw archive (!226, !227): 45 files uploaded, job passed (open, owner's: #33, retention
near the 1 GB quota). Reads: 223 generated, 1005 carried, 13 rejected on "sells" or "selling" (barred since !252).
**Not yet checked (needs a read-only production query, owner approval each time; the local
`.env` has no `SUPABASE_ANON_KEY`):** the BRK-B, BF-B and BT-A.L cards, and that Kojamo
(KOJAMO.HE) and Golden Ocean (GOGL.OL) dropped out. The scheduled Oct 15 run still happens. To run production on demand the owner
asks explicitly: `glab api -X POST projects/rami.al-fahham%2Fstock-explorer-app/pipeline_schedules/4404666/play`
(about 45 minutes, spends AI calls), then read the `generate_assessments` lines of the job log.

**Real-shaped fixtures:** `validate:full` replays recorded payloads against a golden mart. Open: #40.

**Git push auth flakiness:** if it recurs, ask the owner; don't touch the credential store.

**Null-when doc enforcement: MERGED (!207, !210).** `check_null_when_documented` in `check_dbt_documentation.py`; a description that already says "null" can still be incomplete.

**dbt-layer audit: MERGED (!205).** Durable lesson: a "mechanical" rule needing a judgment call
IS the owner's; six review rounds were one undocumented exception invented along the way. Not
acted on: `fct_fundamentals_snapshot` is "latest state" despite the name; staging bypasses
`source()` for `raw_parquet_union()` (freshness still works).

**Durable lessons from merged work (detail in git):** an objective copy defect is a mechanical
fix, only a change to what the copy CLAIMS needs asking; when visual iteration keeps being
rejected as "random", ask what functional categories the elements fall into before tweaking
values; citing past incidents as precedent is not the owner deciding fresh (working-agreement
SS7); when the owner supplies literal wording, use it verbatim; when a fix "feels like a hack",
pattern-matching free text to infer something is the wrong layer, so state it structurally; a
third bug on one feature after two narrow fixes means find the shared root cause. The repo is
`stock-explorer-app` (renamed from stock-swipe-app); GitHub is a one-way public mirror of GitLab.

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
- **!95-!98** (detail in each MR's own `contract.md`/`review.md`): browser-storage coverage,
  Discover/Search nav state loss, README accuracy, Saved-tab confirm + per-item removal. !98's
  planning caught two real bugs first: an out-of-sync "is this saved" check that would have
  stranded a removed ticker, now the shared `saved_keys_with_order()`, and a
  `clear_interactions()`/`st.rerun()` ordering bug.
- **!73-!87** the nine Gemini-feedback points: see those MRs.

## Market coverage

Nine markets active and run in production: US S&P 500, UK FTSE 100, Japan Nikkei 225,
Australia ASX 200, Germany DAX, France CAC 40, Netherlands AEX, Switzerland SMI, Spain
IBEX 35. Six more merged (!230), first production run 2026-10-11 (see In flight). **Read `docs/data_contract.md`'s market activation checklist
before onboarding any of them** (the `onboard-market` skill routes there); it carries the
procedure and two traps no other doc holds (Wikipedia rejecting pandas' default user agent;
`table_index` being positional, and silently wrong on a first refresh).

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

1. **Stale cards: CLOSED (!216).** Evicted by age via the `current_cards` view, rule in
   `docs/data_contract.md` Freshness. Watch on the next run: SATS and ASK ("quote not found"
   on Yahoo) should cross 28 days and leave; the four uk trusts that lost `info.sector` may
   recover by themselves.
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
Run `python scripts/bootstrap.py --verify` before pushing: `docs/development_workflow.md`
"Definition of done". Per-listing deck deduplication is the `current_cards` view (migration
020); the cross-market rule, `dedupe_by_company` in `frontend/explore_filters.py`, is the FE-1
exception recorded in criteria v2 (owner answer A).
`_DECK_TTL_SECONDS`' approved 15-60 minute band sits beside the constant.

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
- **Review mechanics**: the blocking review gate is `.claude/hooks/commit_review_gate.py`
  (a git pre-commit hook, `review-gate` in `.pre-commit-config.yaml`, gating Claude Code's
  commits in whatever checkout git commits). `diff_sha256` covers the branch's
  CUMULATIVE diff: everything committed since the merge-base with `main` plus what is staged,
  with `.claude/task/` excluded (so `review.md` never hashes its own bytes). Get the live hash
  via `python .claude/hooks/commit_review_gate.py --diff-hash` -- use it, do not hand-roll the
  hash; the gate's `[0-9a-fA-F]{64}` pattern never matches `git hash-object` output. The
  verdict parser needs the literal token `VERDICT:` at the START of its own line, and the LAST
  one in a section wins. **The `##` section header itself must be the literal
  required-reviewer name** (`## platform-reviewer`, `## scope-auditor` -- exactly as
  `review_routing.json` spells it), not a round label; a differently-named header reads as
  "no verdict". The roles in `.claude/agents/` register as subagent types, but with only
  Read/Grep/Glob; when a review needs `glab` or pytest, dispatch a `general-purpose` agent
  with the role `.md` inlined. Stage `review.md` before committing: pre-commit hides unstaged
  changes while hooks run. `review.md` can be committed separately for free (`.claude/task/` is hash-excluded);
  this file is NOT excluded, so a separate `active_work.md` commit on a branch with real
  changes needs a refreshed `diff_sha256` first.
- **`review_routing.json` routes by the branch's cumulative PATH list, not by what the change does** -- and two
  patterns can both match one file (e.g. `*.sql` -> analytics-engineer-reviewer AND
  `supabase/*` -> data-engineer-reviewer both match a Supabase migration file), requiring
  both reviewers. The commit gate catches a missed one; re-check routing carefully for any
  file touching more than one obvious category. **A file added to scope mid-task can pull in
  a reviewer never dispatched until the commit gate itself blocks on it** (repo-cleanup
  Phase 3: a `*.sql` file added late needed `analytics-engineer-reviewer`, missed until the
  gate caught it) -- re-check the routing against the branch's FULL cumulative path list, not just
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
- **The guardrails are owned by this repo (issue #26):** hooks in `.claude/hooks/`, reviewer
  roles in `.claude/agents/`, copied once from `claude-project-kit` with no runtime link to it
  or to `dbt-agent-kit`. Change them here, reviewed like code; don't propose re-linking a kit
  or installing hooks globally. A test fails if the `active_work.md`
  budget grows past `handover_in.py`'s cap (32000).
- **Global/machine-shared file edits (`~/.claude/hooks/*`) have broken a sibling project
  before** -- a global hook change once broke `football-data-pipeline`'s review gate. This is
  why MR !116's (a) and (b) sub-items were declined outright (2026-09-15, item 0 above). Don't
  propose one without asking first, and expect "no" as the default answer.
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
  `gitlab`, use `glab`, never `gh`. The branch-protection ordering trap is in
  `docs/development_workflow.md`.
