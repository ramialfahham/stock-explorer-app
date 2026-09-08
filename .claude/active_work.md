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

## Recent work (2026-09-08)

**MR pending -- deterministic style/rule guard for AI-generated card reads,
`find_read_style_violations()` in `scripts/assessment_rules.py`.** Extends the existing
hallucination guard (`validate_read_metrics`) with a sibling check over 6 of
`READ_SYSTEM_PROMPT`'s own rules (dashes, exclamation/emoji, investment-advice language, named
AI-tell phrases, growth-period phrasing, verdict-ending) via regex/string matching -- zero new
Claude spend, zero new infrastructure. Chose this over a periodic LLM-judge eval specifically
because Claude API cost here is already ungoverned (open item 8) and a full LLM-judge was
already declined once on cost grounds (`docs/data_contract.md`); put to me directly before
building anything, since cost/mechanism are owner-only calls.

**A real, useful lesson in how hard "add a regex, don't add a new bug" actually is:** four
consecutive cto-reviewer rounds, each catching a genuine, distinct bug in the PREVIOUS round's
own fix -- round 1: three false positives in the original design (an unbounded "but" search, an
unscoped growth-period phrase, unanchored cheap/expensive/price/worth-it). Round 2's fix for
those introduced two more (a sentence-splitter that broke on the "." in every percentage this
app renders, and a share/stock anchoring exclusion that swallowed legitimate "share of X"/
"market share" vocabulary). Round 3's fix for THOSE introduced two more still (inverted OR/AND
lookaround logic in the decimal-tolerant sentence boundary, and the share/stock exclusion
leaking onto "stock" despite the code's own comment claiming otherwise -- caught only because
the "stock" branch had zero test coverage until then). Round 4 came back genuinely clean after
16 more adversarial counter-examples. Every fix mutation-tested for real at every round. Full
round-by-round account, including a mid-review concurrent-edit-race incident (a reviewer's own
git operation reverted an unrelated concurrent edit, self-caught and disclosed by the reviewer,
logged as a new session memory) in this branch's own `contract.md`/`review.md`.

## Recent work (2026-09-07)

**MR !104, merged** -- repo's first Streamlit `AppTest` end-to-end test,
`tests/frontend/test_app_e2e.py`. Covers the cross-tab Discover/Saved/Search flow (save,
remove, search) unit tests structurally can't reach -- new test infrastructure, not agreed
work; `tests/README.md` documents what exists without asserting a future mandate. Two of my
own claims were wrong, both caught by review and fixed: a false "AppTest never discussed in
this repo" claim (it had been, in a narrower, non-conflicting decision), and an overclaimed
"confirmed, not a production bug" verdict on an AppTest-only crash later traced into real,
shared Streamlit code -- now open item 10 below. Full trace in MR !104's own
`contract.md`/`review.md` history.

## Recent work (2026-09-06)

**MR !100, merged** -- financial-type card capital-adequacy caveat (item 3). New
`FINANCIAL_CAPITAL_ADEQUACY_CAVEAT` constant on every financial-type card regardless of
`ai_read` state. Took 4 equity-analyst-reviewer + 2 scope-auditor rounds: caveat wording
wrongly said "this bank" for the whole GICS Financial Services sector, then twice understated
the card's shown metrics -- final wording states only the one invariant fact rather than
enumerating card contents that can drift.

**Gotcha for future sessions, from that task**: `commit_review_gate.py`'s verdict parser needs
the literal token `VERDICT:` at the start of its own line -- `Round 2 VERDICT: PASS` parses as
no verdict at all, silently. Multi-round `review.md` entries: earlier rounds as prose, only the
final round's verdict as a bare `VERDICT: PASS`/`FAIL`/`ESCALATE` line.

**MR !101, merged** -- scheduled-pipeline alerting + ingestion checkpoint (item 2). Alerting:
GitLab's native "Pipeline emails" integration, zero new code/dependency -- **owner action
still pending, not verifiable as done from here**: Settings → Integrations → Pipeline emails →
your email → "Notify only broken pipelines" → branches = `main` only (documented in
`docs/operations_guide.md`). Checkpointing: `ingestion/yfinance/ingest.py`'s fetch functions
skip tickers/batches already in a same-day `.checkpoint` marker instead of refetching, flush
incrementally, `--force-refetch` bypasses it. Three review rounds caught real defects: a
batch-duplication bug, non-atomic writes, and a freshness check with no protection against two
other scripts (`seed_ci_raw_fixtures.py`, `backfill_fundamentals_parquet_schema.py`) writing
the same paths -- the marker mechanism is the fix for that third one. Landing after !100 meant
a real merge conflict on this file (both branches edited it); resolved by merging `main` in,
and the `frontend/`/`docs/data_contract.md` files that merge carried along were verified
byte-identical to already-reviewed, already-live content -- owner approved skipping a
redundant cto-reviewer/equity-analyst-reviewer re-dispatch on them.

**Finding, not folded into !101 (owner's call):** pulling the real job trace (`2808154517`,
the 2026-09-01 scheduled run) showed ingestion is only ~24 of the ~65-minute total (37%) -- the
actual dominant, ungoverned cost is `generate_assessments.py`'s AI-read step (~39 min, one
Haiku call per changed card, no cap). Logged as open item 8 below.

**MR !103, merged** -- dbt model contract on `mart_stock_cards` (`config: {contract: {enforced:
true}}` + `data_type:` on all 80 columns) + `dbt source freshness` on all three raw sources
(`loaded_at_query` via `raw_parquet_union`, warn 20d/error 30d). `yf_daily_prices` gained a new
`ingested_at` column to make this possible. Five review rounds caught seven real gaps (a
pre-merge-verification gap, an unscoped glob, a mis-cited prior decision, a schema-mismatch
concat bug, a missing batch-isolation test, freshness being table- not per-market -- open item
9 below, and a local-dev-only test gotcha), all fixed and mutation-tested. Full round-by-round
account in MR !103's own `contract.md`/`review.md` history.

## Recent work (2026-09-01 to 2026-09-02)

All nine Gemini-feedback points in
[`docs/backlog/gemini_verdict_feedback.md`](../docs/backlog/gemini_verdict_feedback.md)
shipped (MRs !73/!75/!77/!79/!81/!83/!85/!87; !79 declined sector-relative calibration,
!85 declined moving the pre_revenue threshold) -- that doc now has nothing outstanding.
Full account, including three real review FAILs, in `docs/handover_2026-09-03.md`.

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

**Portfolio-readiness audit, in progress (2026-09-04).** Owner requested a full end-to-end
audit ("this repo has to be portfolio-ready... someone who knows what they're talking about
should say, 'this guy knows his stuff'"). First fixes, MR !97, merged 2026-09-05: README's
live-demo link + Stack table corrected from Streamlit Community Cloud to Render (the actual,
already-shipped deploy target, verified live); `docs/media/discover-card.png` refreshed to
match the current UI (old screenshot showed a stale tagline, old verdict-copy style, and a
"Forward P/E" metric no longer on the card). Remaining portfolio items not yet started: GitLab
topics sync, project description, a custom link-preview/avatar image.

**Owner decision on repo visibility (2026-09-08): go public once the repo is portfolio-grade,
not before.** Sequencing, not a standing block -- the repo stays private through the remaining
polish work (topics/description/link-preview image, and whatever else "portfolio-grade" turns
out to need) and flips public as the last step, not a precondition to start on the rest. Don't
treat visibility as something to decide independently of that polish work finishing.

All three sibling branches from this stretch of work are merged into `main` as of 2026-09-05:
MR !95 (`test/browser-storage-coverage`), MR !96 (`fix/discover-search-nav-state-loss`, Open
item 4 below), MR !97 (`docs/portfolio-readme-accuracy-fixes`, above).

**Saved-tab confirm + per-item removal, in progress (2026-09-05), branch
`feat/saved-clear-confirm-remove`.** Two owner-decided product fixes from a "what product work
is left" review: "Clear saved" (the bulk wipe in the "⋯" menu) now confirms in place before
acting (two-click, session-state-driven label swap -- no second nested popover, since
`st.popover` shouldn't nest); a single saved company can now be removed on its own (previously
only the all-or-nothing bulk clear existed). Planning turned up a real, scope-expanding bug
before any code was written, escalated and approved: `frontend/explore_filters.py` had its own
separate "is this saved" copy (no concept of reversal) feeding Discover's saved-exclusion
filter -- shipping per-item removal without fixing it would have made a removed ticker vanish
from Saved but stay excluded from Discover forever, with no way back in since Search has no
Save action. Fixed by a single shared `saved_keys_with_order()` helper in
`explore_filters.py` that both the Discover-pool filter and the Saved tab's own count/list now
delegate to, so the two can never disagree again. A second real bug caught during plan
validation, before shipping: `clear_interactions()` ends with its own `st.rerun()`, which halts
the rest of the script run, so the confirm-flag reset had to be reordered to fire *before* that
call, not after, or the confirm prompt would get stuck reopening with an impossible "Clear all
0 saved companies?". Both bugs verified fixed by hand against the running dev server, not just
reasoned about. Full account, review trail, and a scope-auditor correction round (2 stray em
dashes, one file missing from `scope_paths`, a stale `_saved_keys_with_order` name, and
strengthening the per-item-removal decision's owner-visibility trail) in this branch's own
`.claude/task/contract.md`/`review.md`.

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
   this pattern shows up on more tickers. **Still separately open, not resolved by the above:
   there is no eviction mechanism** -- a ticker that stops being exported keeps its last card
   in the deck indefinitely (frontend dedupes to newest row per ticker, not newest snapshot).
   Whether the deck should evict by snapshot age remains an owner call.
2. **The growth metric's card copy tension** ("One quarter can be noisy, so look for a
   pattern over time") sits on cards the growth gate can downgrade on exactly one quarter --
   owner's call, not resolved.
3. **The financial-type card's capital-adequacy blind spot, fixed and merged (MR !100).**
   Previously survived only
   as an LLM prompt instruction with no card-face caveat, so a card with a null `ai_read`
   warned nobody. Fixed with a deterministic, owner-approved caveat ("These numbers do not
   show whether this company holds enough capital to stay safe.") that now shows on every
   financial-type card regardless of `ai_read` state, since the prompt only asks the model to
   mention the limit, never guarantees it does (`frontend/card_copy.py`'s
   `FINANCIAL_CAPITAL_ADEQUACY_CAVEAT`, rendered by `frontend/card_ui.py`). Two review rounds
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
6. **Free-tier Supabase pauses after ~7 days idle** ("Could not load cards", a real bug in
   `_ensure_all_cards`), never resolved -- and the current biweekly pipeline schedule
   (1st/15th) creates gaps up to ~15 days between writes, longer than the pause threshold.
   Worth checking whether this is silently affecting production right now, and deciding
   keep-alive vs. a paid tier.
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
