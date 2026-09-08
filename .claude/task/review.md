# Review

diff_sha256: fb85701f25fd6a88be39d9d246256f935a1f8719939d3e9a755766f2481bc97c

Five rounds. Both required reviewers (scope-auditor by `always`, cto-reviewer by `frontend/*`
and `tests/*`) ran cold and read-only against the staged diff each round. Earlier rounds are
prose below; only each section's final round carries a bare verdict line.

## Measured result (contract `done_when`)

Against live production Supabase, same script both ways:

| | Round trips | Payload | Time |
|---|---|---|---|
| Before (`select=*` deck + assessments) | 7 | 18.38 MB | 7.80s |
| After (slim deck) | 5, plus 1 export probe = **6** | 1.46 MB | 1.87s |
| After, per card opened | 2 | ~4 KB | 0.61s |

12.6x payload cut, 4.2x faster on the deck fetch. The larger real-world win is not in this
table: 18 MB of JSON is no longer parsed and deduped in Python on a free-tier shared-CPU
Render instance for every first-time visitor.

**This misses the approved plan's own estimate** (~150-250 KB over 1-2 round trips); see the
contract's DELIVERY SHORTFALL amendment. Not claimed and not measured: browser first-paint
timing from a fresh incognito session, which an earlier `done_when` draft promised.
Verification of the rendered result was a manual end-to-end pass against the running dev
server (card face with `ai_read`, verdict, `business_summary`, sector range marks; Saved with
headlines; Search by name), plus 604 automated tests.

## scope-auditor

Round 1 returned FAIL on six findings: `docs/supabase_setup.md` told operators a hard refresh
reloads the deck, which the cross-session cache made false; the contract justified the export
probe as costing nothing on the cold path, which a `st.popover`'s eager body makes untrue; the
30-minute TTL shipped against a `decisions_reserved` entry with no recorded answer;
`.claude/active_work.md` was in scope but unmodified; `done_when` promised first-paint numbers
that did not exist anywhere; and a backlog doc described the old fetch path in the present
tense. All six fixed. The TTL was resolved by citing the approved plan's own 15-60 minute
band as the recorded authority, which the reviewer then verified independently against the
plan file rather than accepting the citation.

Round 2 passed, with two advisories: the handover had 809 bytes of headroom under its
32,000-byte cap, and the delivered numbers miss the approved plan's estimate. Both acted on.

Round 3 returned FAIL on three: an unverified causation claim at `active_work.md:17` ("the
UptimeRobot ping keeps it warm", contradicting open item 6's own "nobody has confirmed which
URL the ping targets"); a stale test count; and a contract with no round-2 amendment, leaving
the delivery shortfall disclosed only in the handover and not in the artifact that travels
with the MR. All three fixed.

Round 4 passed, flagging as non-blocking that open item 6's heading still asserted the
causation its body qualified. Fixed rather than shipped, which is what round 5 confirms.

Round 5 proved the single-line delta by reconstruction rather than assertion: it recovered the
round-4 staged blob from the object store, rebuilt that round's diff through a separate index,
and matched the round-4 hash byte-for-byte.

VERDICT: PASS
risks_checked:
- Scope: all 12 staged paths inside `scope_paths`, including the three added by amendment
  (`frontend/overflow_menu.py` after it proved to be a second consumer of the renamed guard,
  and the two docs the change made stale).
- No em/en/figure dash on any added line, scanned from a file with explicit UTF-8 decoding
  rather than through Python stdin, which mis-decodes silently on this machine.
- `.claude/active_work.md` at 30,427 bytes, under the 32,000-byte SessionStart injection cap,
  with the `VERDICT:` parser gotcha and the pending owner action for GitLab pipeline emails
  both confirmed to have survived the collapse of merged history.
- No §6 owner-only decision taken unilaterally: caption copy byte-identical, `_hydrate` reuses
  an existing error string, the load spinner deferred because its text would be new copy, and
  retiring the redundant export caption left to the owner.
- `is_undefined_column_error` judged ordinary error handling inside an approved change, not a
  new mechanism: it restores pre-branch behaviour rather than creating any.

## cto-reviewer

Round 1 returned FAIL on four. The serious one: `deck_rows_lack_columns` could not invalidate
the cache it guarded, because `_ensure_all_cards` cleared only `session_state` while
`_cached_deck.clear()` was never called, so firing the guard produced an unrecoverable spin
rather than a recovery; and its docstring's premise that the cache "outlives a deploy" is
false for `persist=None`. Also: no test pinned `DECK_COLUMNS` against the fields the list
paths actually read, and the fixture derived its keys from `DECK_COLUMNS`, making the suite
self-referential; the export probe cached a swallowed exception as "no problem" for a full TTL
window; and a new user-visible error string had been added while the contract reserves
user-visible copy. All four fixed.

Round 2 returned FAIL on three more. The real bug: `_descriptions_missing` swallowed every
exception into `False`, including PostgREST's 42703 for a missing `business_summary` column,
which is exactly the pre-migration-004 state the overflow menu's caption exists to announce.
The guard failed open on its own trigger. Fixed with `is_undefined_column_error()`. Also two
false numbers of mine: the cold-path round-trip headline said 5 when the eagerly-computed
popover probe makes it 6, and a handover claim that the ping reaches Supabase "because the
card fetch is uncached per request" was true before this branch and false after it.

Round 3 confirmed all seven prior findings closed, verified the 42703 detection against the
installed `postgrest` 2.30.0 rather than assuming its error shape, independently
mutation-verified the `_cached_deck.clear()` test, and confirmed from
`streamlit/runtime/caching/cache_utils.py` that a raised exception is genuinely never cached.
It returned FAIL on one thing: a test count corrected from one wrong number to another.
Fixed by deriving it from the suite instead of typing it.

Rounds 4 and 5 passed. Round 5 proved no code moved since round 3 by reconstructing round 4's
staged diff from the recovered blob and matching its sha256 exactly.

VERDICT: PASS
risks_checked:
- Column completeness: every field read by `filter_pool`, `sectors_for_market`,
  `eligible_counts_by_market`, `latest_snapshot_label`, `saved_row_subtitle`,
  `lead_metric_for_row`, `metric_label`, `format_metric_value`, `row_ui` and app.py's
  title/sort lambdas independently traced against `DECK_COLUMNS`. Nothing read is unfetched.
  `health_verdict`/`ai_read` are read only by `card_ui.py`, which always receives a hydrated
  row, so dropping the assessments join from the deck causes no list-row regression.
- Cache safety: constant key is correct here because the deck is public market data; user
  interactions stay in browser storage and never enter the cached payload. A raised exception
  is not stored, so a transient failure retries rather than persisting for a TTL window.
- `_hydrate`'s slim-row fallback actually renders: no direct `card["..."]` indexing exists in
  `card_ui.py`, `card_copy.py` or `saved_news.py`, so a failed detail fetch degrades.
- Both mutation checks re-verified independently by the reviewer, not accepted from the
  builder: removing `_cached_deck.clear()` drops the second fetch, and reverting the guard to
  its old `business_summary` form produces 3 fetches where the shipped code produces 1.
- Two disclosed behaviour differences in the rescoped export check (empty eligible set now
  answers "missing"; whitespace-only summaries count as present), both left unfixed on the
  grounds that detecting them costs a cold-path round trip for states that already render
  correctly, and `scripts/check_export_health.py` gates fill at source.
- Platform surface: no new dependency, CI job, hook, service, secret or schedule change; only
  `typing.Callable` newly imported, from stdlib. `_paginate` is a pure read, idempotent on
  re-run.
