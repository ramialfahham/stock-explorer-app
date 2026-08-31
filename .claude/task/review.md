# Review

diff_sha256: c2f81fce2c56815b093fb220d2b3e76fbf0a60c2fb483867fa0e3c2ae00335a9

Two review rounds. Required reviewers per routing (`.claude/review_routing.json`):
scope-auditor (always), cto-reviewer (`frontend/*`, `tests/*`). No dbt or `docs/data_contract.md`
file in this diff, so analytics-engineer-reviewer and equity-analyst-reviewer are not required.

**Reviewer dispatch:** the plugin's reviewer agent types are not registered as dispatchable in
this session, so each ran as a general-purpose agent instructed to read its own role file
verbatim first. Cold, blinded, read-only input; the staged index was frozen to a patch file and
sha256 before every dispatch and never moved while reviewers were running. Round 2's
scope-auditor dispatch was interrupted by a Claude Code crash mid-run; the crashed agent was not
resumable in the fresh session and was re-dispatched cleanly against the same frozen diff rather
than trusting a partial transcript.

**Final verdicts (round 2, the commit gate):** scope-auditor PASS, cto-reviewer PASS.

## What this is

Fixes the click-latency problem the owner reported after the Discover pagination fix (MR !70)
shipped: "substantially faster... but still delayed 1-2 seconds." Diagnosed with temporary
server-side timing instrumentation (not shipped, removed before this diff was staged -- the
earlier browser-side JS-timer approach used to verify MR !70 was found unreliable, throttled on
a reported-hidden preview tab). Found: `get_anon_client()` (`frontend/supabase_client.py`)
rebuilt a brand-new Supabase client via `create_client(url, key)` from scratch on every single
Streamlit script rerun, measured at ~1.06-1.09s per call, versus ~0.12-0.18s for everything else
in a run combined. Because `frontend/row_ui.py`'s row click handler calls `st.rerun()` right
after registering a click, this cost was paid twice per click, closely matching the reported
1-2s. Fixed with `@st.cache_resource`, Streamlit's own primitive for an expensive-to-construct,
shareable resource with no per-user state. Live-verified post-fix: two clicks measured at ~0.30s
and ~0.47s total click-to-response, down from ~1.2-1.4s for a single run pre-fix.

## Round-by-round findings and fixes

**Round 1**: scope-auditor FAILED on two internal-consistency defects in the new
"Discover click latency" handover entry: (a) its heading said "reviewed" while its own Status:
line, left as unedited context, said "review in progress"; (b) a cross-reference elsewhere in
the file quoted the OLD heading text of a different entry ("Discover list paginated") verbatim,
but this same diff renamed that heading to "MR !70 MERGED, 2026-08-31: Discover list paginated."
Both fixed. Separately, cto-reviewer FAILED on a real test gap:
`tests/frontend/test_supabase_client.py`'s credential-missing test called `get_anon_client()`
only once, which cannot distinguish a correct fix from a regression where the failure itself
gets cached (a second call under the same failure condition silently returning something falsy
instead of re-raising). Fixed: the test now calls it three times in a loop and asserts
`RuntimeError` on each.

**Round 2**: cto-reviewer independently mutation-tested the round-1 test fix -- wrote a
hypothetical regression (a version that caches the exception and returns `None` on retry),
confirmed the round-1 single-call assertion would have passed against it (bug hidden) while the
round-2 three-call version correctly fails on the second call -- and independently confirmed
`st.cache_resource` does not cache exceptions in this repo's pinned Streamlit version. PASSED.
scope-auditor's dispatch crashed mid-run (Claude Code process crash, unrelated to the diff) and
was re-dispatched cleanly against the same frozen diff; verified all three round-1 fixes landed,
re-ran the full grep sweep for any other stale cross-reference to the renamed heading (none
found), and re-confirmed `pytest` (430 passed) and the em/en-dash rule independently. PASSED.

## scope-auditor (round 2, final)
VERDICT: PASS
risks_checked:
- Whether `@st.cache_resource` counts as a new mechanism requiring escalation: `st.cache_data`
  (the sibling primitive) is already established practice in this codebase
  (`frontend/saved_news.py`, documented in `docs/ux_principles_finanz_lern_apps.md`) --
  `cache_resource` is the same family of built-in framework primitive, not a new
  dependency/service/framework.
- Both round-1 fixes verified landed and no other stale cross-reference to the renamed heading
  survived anywhere else in the file or repo.
- `scope_paths` respected exactly; `decisions_reserved: none` accurate against the default
  owner-decision list (this only changes how often an existing client object is constructed,
  reducing cost, not raising it).
- No doc-sync gap: only `docs/backlog/discover_list_performance.md` references this behavior,
  and it's updated in this same diff.
- UX PR gate correctly not triggered: backend caching only, zero UI/copy/interaction change.
- `impact_map`'s "single call site" claim confirmed via grep (`frontend/app.py:532`, only one).
- No em/en dash on any added line; `pytest` claim (430 passed) independently re-run and
  confirmed, including that the credential-missing test genuinely loops three times.

## cto-reviewer (round 2, final)
VERDICT: PASS
risks_checked:
- Mutation-tested the round-1 test fix directly: wrote a hypothetical regression that caches
  the exception and returns `None` on retry, confirmed the round-1 single-call version would
  have passed against it (bug hidden) while the round-2 three-call version fails on the second
  call -- the fix genuinely closes the gap, not just superficially.
- Independently probed `st.cache_resource` (this repo's pinned Streamlit version) directly:
  confirmed it does not cache exceptions -- a decorated function that raises re-executes and
  re-raises on every subsequent call, matching the test's premise.
- Core fix re-verified fresh: `@st.cache_resource` on `get_anon_client()`, single call site
  (`frontend/app.py:532`), no change to `create_client()`'s own call, query logic, or auth scope.
- Full suite re-run fresh: 430 passed (428 baseline + 2 new), including the new test file in
  isolation.
- Doc-consistency fixes verified by reading the current file, not just the diff: the click
  latency entry and the renamed MR !70 entry are in the correct order, and the downstream
  cross-reference matches the actual renamed heading.
- No em/en dash on any added line, scanned programmatically. Scope discipline: every file in
  the diff matches `scope_paths`; no new dependency, service, lifecycle hook, or workflow step.
