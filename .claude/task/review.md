# Review

diff_sha256: 3d9f7a9a72d07f83b1375e379c913903c938047d0693aa412f60889718c21dd3

## scope-auditor
Round 1 FAILED (one finding)
- The contract's objective claimed `git log --all -S"AppTest"` returns "zero hits, ever,"
  carried over unverified from an earlier exploration pass in this session rather than
  re-checked before being asserted. False: the command returns 5 real commits, two of which
  (`702bfb62`, `0bb8997c`) explicitly discuss AppTest -- a prior task (two small Streamlit
  widget-persistence bugfixes) considered and declined it as disproportionate for that fix's
  scope, verifying instead by direct dev-server interaction. Read in full, that decision
  doesn't conflict with this task (a dedicated, owner-approved decision to build AppTest
  coverage as its own infrastructure), but the false "zero hits, ever" claim erased a real,
  on-point precedent instead of engaging with it. Same disclosure-accuracy class as item 3's
  MR !101 mis-citation.

Everything else verified clean: staged diff matches scope_paths exactly (`.claude/active_work.md`
correctly not yet touched); all button/widget key claims traced directly against `app.py`/
`row_ui.py`/`nav_pages.py`; `_FakeLocalStorage` and the seeded interaction row shape confirmed
to match `test_browser_storage.py`/`browser_storage.py` exactly; 5/5 tests pass standalone,
536/536 full suite; all 5 tests have discriminating assertions, not tautologies;
`tests/README.md`'s new paragraph is purely descriptive, asserts no future mandate; review
routing (scope-auditor + cto-reviewer only) confirmed correct against `.claude/
review_routing.json`; em/en-dash scan (file-based, explicit UTF-8): 0 hits.

Resolution: corrected the objective with the real `git log` history, quoted the actual prior
decision's reasoning, and explained plainly why it doesn't conflict with this task rather than
erasing it. See `contract.md`'s amendments.

Round 2 (re-check of the corrected objective only, nothing else in scope):
VERDICT: PASS
risks_checked:
- Re-ran `git log --all -S"AppTest"` independently: exact same 5 hashes cited, confirming the
  history claim is complete, not cherry-picked.
- Read `702bfb62` and `0bb8997c` in full (not just the quoted fragment): the quote is
  verbatim-accurate, `0bb8997c` is genuinely that fix's own review record, and both are
  explicitly scoped to one small bugfix's proportionality -- the "narrow, non-conflicting"
  characterization holds against the primary source, not spin.
- Cross-checked `test_app_e2e.py`/`tests/README.md` against round 1's specific factual claims:
  all match; the only prose change is the disclosed cto-reviewer docstring fix.
- `git status --short` confirms the staged file set is exactly scope_paths minus the
  still-pending `active_work.md` -- no extra file swept in by either correction.
- Process note, not folded into the verdict: `.claude/task/review_input.patch` on disk is
  stale debris from the prior (item 3) task -- gitignored, untracked, no impact on this
  review or anything committed. Left alone, out of scope to clean up here.

## cto-reviewer
Round 1 FAILED (one finding)
- The test docstring and contract both claimed, after a single manual dev-server pass with no
  crash observed, that the AppTest stale-widget `KeyError` was "confirmed... not a production
  bug." Overclaimed. Independently traced the real mechanism: `AppTest`'s `LocalScriptRunner`
  subclasses Streamlit's own production `ScriptRunner` unmodified; the cleanup path raising
  this `KeyError` (`session_state.py`'s `_compact_state`) is real, shared production code --
  which itself wraps this exact case in `except KeyError: pass`, citing a known upstream
  Streamlit issue (`streamlit/issues/7206`) about stale widget metadata. The underlying
  condition (viewing two different cards' metric-playground panels swaps the active widget-key
  set) is real, not AppTest-specific; what's AppTest-specific is that `element_tree.py`'s
  `get_widget_states()` reads widget state without production's own defensive swallowing,
  turning a condition production tolerates silently into a hard test failure. One manual pass
  not reproducing a crash is consistent with this, not proof against a rarer path still being
  a real problem in production.

Also confirmed clean, independently verified: CI/operational risk (no new job needed, `AppTest`
needs no browser/display, dependency claim verified true against `requirements.txt`); runtime
cost measured directly (5 tests in ~11s, full suite in ~19s -- noted as a new cost precedent,
not blocking); all four mocking boundaries verified correct against source, not trusted from
comments; `_assert_clean`'s reasoning verified sound against `_load_cards()`'s actual
exception-to-`st.error()` handling; all button/widget keys verified 1:1 against `app.py`; scope
confirmed via `git diff HEAD --stat` (only the 4 expected files); no secrets, no CI-authority
file touched; em/en-dash scan: 0 hits.

Procedural note: while independently re-verifying the mutation-test claim, accidentally edited
`frontend/app.py`, self-caught it (blocked by the auto-mode classifier before the follow-up
pytest call), reverted immediately via `Edit`, and confirmed clean via `git status`/`git diff
HEAD --stat`. Independently re-verified this claim afterward: confirmed exactly the 4 expected
files staged, `frontend/app.py` not among them.

Resolution: corrected the test docstring and contract's amendments to state the mechanism
accurately (real, shared, production-tolerated condition; AppTest-specific only in that it
lacks the same defensive swallowing) instead of the overclaimed "not a production bug." Flagged
to the owner as a genuinely open question in the final chat report, not silently closed and not
unilaterally turned into a tracked issue.

Round 2 (re-check of the corrected docstring/amendments only, nothing else in scope) FAILED
(one finding):
- The round-1 fix itself introduced a new, unverified mechanism claim: the corrected docstring
  stated `_compact_state` is "called from the same `ScriptRunner.on_script_finished` that
  `LocalScriptRunner` subclasses unmodified." Wrong on both parts, checked against the
  installed Streamlit 1.57.0 source: `_compact_state`'s only call site is
  `SessionState.on_script_will_rerun` (session_state.py:641), invoked from
  `ScriptRunner._run_script`'s closure (script_runner.py:638) -- gated on
  `rerun_data.widget_states is not None`, at the start of the NEXT run.
  `on_script_finished` is a different `SessionState` method entirely (no call to
  `_compact_state` anywhere in that path), reached via `ScriptRunner._on_script_finished`
  (script_runner.py:749) -- which `LocalScriptRunner` does NOT inherit unmodified, it
  redefines its own copy (local_script_runner.py:154). The method that actually IS inherited
  unmodified and relevant here (`_run_script`) wasn't named at all. Confirmed contract.md's
  own amendments were NOT affected -- they already used the same general, defensible phrasing
  as this reviewer's round-1 finding, not the specific wrong claim.

  Also confirmed clean in this round: open-question framing landed correctly, not overshot
  (hedges both directions, never asserts "this IS a production bug" either); the
  `except KeyError: pass` / issue-7206 citation itself is accurate (verified against
  session_state.py:440-451, comment cites the URL verbatim); the procedural note about the
  accidental `frontend/app.py` edit is accurately recorded in both `review.md` and
  `contract.md`, cross-verified against current repo state (all empty diffs); nothing else in
  the diff changed beyond the two named corrections.

Resolution: corrected the docstring to the verified chain -- `_compact_state` <-
`SessionState.on_script_will_rerun` <- `ScriptRunner._run_script` (a method `LocalScriptRunner`
does not override, so it runs unmodified there too). Independently re-verified the exact same
way before writing the fix: grepped `_compact_state`/`on_script_will_rerun`/
`_on_script_finished` across all three files, confirmed `_run_script` is absent from
`LocalScriptRunner`'s override list.

Round 3 (re-check of the corrected mechanism chain only) -- re-derived fresh from installed
source rather than trusting the round-2 writeup, since this was the third round on the same
claim:
VERDICT: PASS
risks_checked:
- `_compact_state`'s call graph: repo-wide grep across the installed `streamlit` package shows
  exactly one call site (`session_state.py:641`), inside `SessionState.on_script_will_rerun`
  (633-643) -- the docstring's "called by" claim is exhaustively true, not just spot-checked.
- `on_script_will_rerun` really executes inside `ScriptRunner._run_script`: the call
  (`script_runner.py:638`) sits inside closure `code_to_exec` (626), and that closure is
  actually invoked at line 705 -- both within `_run_script`'s body (470-748) -- not just
  lexically nested without a real call.
- `LocalScriptRunner`'s complete override surface (8 methods, grepped fresh) excludes
  `_run_script`, confirming it truly runs unmodified under AppTest; installed version
  independently confirmed as 1.57.0, matching what the claim is checked against.
- Diff scope confined to the 4 expected files; the corrected sentence appears exactly once;
  every other mention of this mechanism in the diff is consistent historical narrative, not a
  live contradicting claim.

All required reviewers now PASS against the current, fully-staged diff: scope-auditor round 2,
cto-reviewer round 3.
