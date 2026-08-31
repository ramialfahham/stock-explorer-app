# Review

diff_sha256: ef7dba706512be96d31aa59271afda93c6c39f1eb74ff966b49a50f793a1b344

Two review rounds. Required reviewer per routing (`.claude/review_routing.json`): scope-auditor
(always). No other pattern in the routing matches this file set (a new `docs/backlog/*.md` file
plus `.claude/active_work.md` and `.claude/task/contract.md`), so no other reviewer is required.

**Reviewer dispatch:** the plugin's reviewer agent types are not registered as dispatchable in
this session, so scope-auditor ran as a general-purpose agent instructed to read its own role
file verbatim first. Cold, blinded, read-only input; the staged index was frozen to a patch file
and sha256 before every dispatch and never moved while the reviewer was running.

**Final verdict (round 2, the commit gate):** scope-auditor PASS.

## What this is

Scopes the Discover list's performance problem as its own backlog item, the fourth pure
scoping/decision task this session. Adds `docs/backlog/discover_list_performance.md`, cleanly
separating what's confirmed by direct measurement (the list mounts ~923-931 individual
`st.button` widgets and ~20,600 DOM nodes unconditionally on every render, no pagination or
windowing, which measurably slows click registration: ~2.4s with the full list vs ~0.6-0.7s with
a 39-row filtered list) from a code-grounded but not yet empirically confirmed hypothesis (that
`_render_tappable_rows`'s `st.rerun()` call, sitting inside the per-row click handler, aborts and
restarts the script mid-loop with a cost proportional to the clicked row's position, explaining
a separately-observed inconsistent server-side run duration). Lists open questions (pagination
vs. alternatives, page size, whether the `st.rerun()` hypothesis needs its own profiling spike,
interaction with the already-decided "first-time Discover default" scope, Saved's exposure)
without resolving any of them, since a widget-count fix is a user-facing product/UX decision
reserved to the owner. Replaces the stale "not yet scoped" note left by the immediately-prior
verdict-dot task in `.claude/active_work.md`. Documentation only: no code, no CI, no new
dependency.

## Round-by-round findings and fixes

**Round 1**: passed overall, with one minor, non-blocking mis-attribution found and fixed in the
same round's write-up: the doc credited the list's sort step to `explore_filters.filter_pool`,
when the sort is actually a separate `pool.sort(...)` call in `app._discover_pool`, right after
`filter_pool` returns. scope-auditor independently re-derived every other code-level claim in the
doc against the actual source (`frontend/row_ui.py`'s per-row `st.container()`/`st.markdown()`/
`st.button()` structure and the exact placement of `st.rerun()` inside the click handler,
`frontend/supabase_cards.py`'s bulk-fetch-and-cache pattern, `frontend/card_copy.py`'s
precomputed sector-benchmark columns), and specifically verified the doc never blurs the
confirmed measurements with the unconfirmed `st.rerun()` hypothesis into one claim. Fixed: the
sort-attribution sentence corrected to name the actual function.

**Round 2**: the fix verified against live source (confirmed `filter_pool` has no sort call and
`_discover_pool` calls `pool.sort(...)` immediately after `filter_pool` returns, exactly as the
corrected wording states), and confirmed narrowly scoped by diffing the round-1 and round-2
patch files directly: only the one sentence and one new contract bullet changed, nothing else in
the doc's conclusions moved. Confirmed clean.

## scope-auditor
VERDICT: PASS
risks_checked:
- Every code-level claim in the doc checked against live source, not accepted on plausibility:
  `frontend/row_ui.py`'s one-container/one-markdown/one-button-per-row structure and the exact
  placement of `st.rerun()` inside the per-row click handler; `frontend/supabase_cards.py`'s
  bulk fetch and session-state caching; `frontend/card_copy.py`'s precomputed
  `sector_median_*` columns (never computed live); `frontend/explore_filters.py`'s
  `filter_pool` (single linear pass, set lookups, no nested loop) and `frontend/app.py`'s
  separate `pool.sort(...)` call, confirmed as two distinct steps after the round-1 finding.
- Confirmed-vs-hypothesis honesty: every mention of the `st.rerun()`-mid-loop mechanism in both
  the backlog doc and the handover is explicitly hedged ("not yet confirmed," "if the
  hypothesis holds"), never asserted as settled fact.
- No owner-reserved product/UX decision silently made: the "Candidate directions" section
  states no ranked or default option, explicitly headed "not decisions, for owner discussion";
  the one "working recommendation" (pagination) lives only in `.claude/active_work.md`,
  explicitly labeled not yet approved.
- Round-1's fix verified narrowly scoped: diffed the round-1 and round-2 patch files directly,
  confirming only the one corrected sentence and one new contract bullet changed, with
  `.claude/active_work.md` byte-identical between rounds.
- Scope: exactly the three files in the contract's `scope_paths` were touched; no code, test,
  CI, or dependency file in the diff.
- No em/en dash on any added line, scanned programmatically across the full patch both rounds
  (199 added lines in round 2, zero hits).
- Both hash checks passed each round: the frozen patch's sha256 and a fresh
  `git diff --staged --no-renames --no-abbrev | sha256sum` on the branch were identical every
  time, confirming the staged index never moved during review.
