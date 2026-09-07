# Task contract

objective: Add the repo's first Streamlit `AppTest`-based end-to-end test, covering
  `frontend/app.py`'s cross-tab Discover/Saved/Search flow (save a card, remove a saved card,
  search by ticker) -- a class of bug the existing pure-function unit tests structurally
  cannot reach, since they never instantiate the real script or a real session.

  Referred to loosely as "item 4" of an earlier 5-item portfolio-readiness list, but that
  number is not asserted here: the list's own source text is confirmed permanently lost from
  this repo (repo-wide grep for "4-persona"/"5-item": zero hits). The prior task in this same
  loose sequence (item 3, MR !103) already proved once that a remembered number from this list
  can be wrong. This contract describes the task by content only.

  Correction (scope-auditor round 1 caught this): an earlier draft of this objective also
  claimed `git log --all -S"AppTest"` returns zero hits "ever," offered as supporting evidence
  that AppTest has never been discussed in this repo. That claim was false -- never re-verified
  against the actual command myself before writing it, carried over unchecked from an earlier
  exploration pass in this session. The real history: `git log --all -S"AppTest"` returns 5
  commits (`702bfb62`, `0bb8997c`, `4986cd61`, `3d2c7c99`, `c77d6d48`), all already in this
  branch's own ancestry. Two of them (`702bfb62`, its `0bb8997c` review record) directly discuss
  AppTest: that task -- two small Streamlit widget-persistence bugfixes -- explicitly considered
  and declined it, reasoning "a plain pytest unit test can't exercise [this] without either
  Streamlit's heavier `AppTest` harness or refactoring the render functions themselves, both
  bigger asks than this fix," verified instead by direct interaction against a running dev
  server. Read in full, not just cited: that was a proportionality judgment for one small,
  unrelated fix, not a repo-wide rejection of AppTest as a mechanism -- it does not conflict
  with this task, which is a dedicated, owner-approved (via `ExitPlanMode`) decision to build
  AppTest coverage as its own infrastructure, not something bolted onto an unrelated change.
  Stated plainly because burying a real, on-point precedent instead of engaging with it would
  be the same disclosure failure the immediately-prior task (item 3) was caught on.

  Unlike item 3 (which enacted a standard `docs/engineering_standards.md:223` had already
  written down and never acted on), **no existing policy calls for end-to-end frontend
  testing** -- today's stated frontend test policy (`tests/README.md`,
  `docs/engineering_standards.md` §3) is unit-level only, by explicit design (existing
  `tests/frontend/*` tests extract pure helpers specifically to avoid touching real Streamlit
  widget rendering; `test_app.py`'s own comment states full-script rendering is currently a
  deliberate unit-test exemption). This task establishes new test infrastructure, not agreed
  work being completed. Full reasoning, technical verification (row-button key patterns traced
  directly in `app.py`, AppTest's actual execution model traced in Streamlit's own
  `script_runner.py`/`local_script_runner.py`/`element_tree.py`), and the concrete mocking
  strategy are in the approved plan: `C:\Users\Rami\.claude\plans\groovy-churning-scroll.md`.

scope_paths:
  - tests/frontend/test_app_e2e.py (new -- the AppTest suite itself)
  - tests/README.md (new paragraph documenting what this file covers and why it's structurally
    distinct from the rest of tests/frontend/)
  - .claude/active_work.md
  - .claude/task/contract.md
  - .claude/task/review.md

decisions_reserved: none outstanding. Two implementation-level choices, disclosed as
  agent-executable, not product content: (1) which 5 flows get coverage (Discover pool render,
  save-then-appears-in-Saved, scoped remove-from-Saved, search-finds-ticker,
  search-no-match-warning) -- chosen because they're the cross-tab session_state interactions
  unit tests structurally can't reach, not a product decision; (2) `frontend/app.py` is the
  AppTest target, not `streamlit_app.py` -- a technical choice (traced in Streamlit's own
  `script_runner.py` that the AppTest target is always freshly re-executed as `__main__` on
  every `.run()`), not a design tradeoff needing sign-off. NOT deciding, and explicitly out of
  scope: whether AppTest coverage becomes a required pattern for future frontend work going
  forward -- that would be a repo-wide testing-policy mandate, a bigger call than this task
  makes; `tests/README.md`'s new paragraph documents what exists, without asserting a mandate.

done_when:
  - `tests/frontend/test_app_e2e.py` exists with 5 passing tests (discover-renders,
    save-appears-in-saved, scoped-remove, search-finds, search-no-match), each driving the real
    app via `AppTest.from_file("frontend/app.py")`, not a direct-import shortcut.
  - Three real I/O boundaries stubbed at their actual call site (verified against source, not
    assumed): Supabase (`supabase_cards.fetch_eligible_cards_with_assessments`,
    `supabase_client.get_anon_client`, plus `SUPABASE_URL`/`SUPABASE_ANON_KEY` env vars),
    yfinance news (`saved_news._fetch_news` -- found only by grepping for network calls, not
    part of the obvious Supabase surface), and browser localStorage (reusing
    `test_browser_storage.py`'s existing `_FakeManager`/`_mount_manager` pattern, not inventing
    a new one).
  - `pytest tests/frontend/test_app_e2e.py -v`: 5/5 pass, standalone.
  - `pytest tests/ -q`: full suite passes, confirming no cross-file conflicts (each `AppTest()`
    instance owns its own fresh session by construction -- verified for real, not assumed).
  - At least one assertion mutation-tested for real: break the thing a test is supposed to
    catch (e.g. make saved-removal not scope to the selected card), confirm the corresponding
    test fails with the expected symptom, restore, confirm green again.
  - `tests/README.md` documents the new file's coverage and its structural difference from the
    rest of `tests/frontend/` (full-script simulation vs. direct-import pure-helper tests).
  - No em/en-dash on any added line (file-based UTF-8-explicit scan, not stdin).
  - Review cycle: scope-auditor + cto-reviewer (both required per `.claude/review_routing.json`
    -- `tests/*` routes to cto-reviewer; no dbt/.sql/ingestion/data_contract files touched, so
    no analytics-engineer-reviewer/data-engineer-reviewer/equity-analyst-reviewer needed).

impact_map:
  - No user-visible change, no production code touched (test infrastructure only).
  - No dbt/ingestion/Supabase files touched -- `analytics-engineer-reviewer`,
    `data-engineer-reviewer`, `equity-analyst-reviewer` are NOT required this time (routing
    checked directly, not assumed carried over from the last task).
  - `tests/*` touched -> requires cto-reviewer per `.claude/review_routing.json:12`.
  - scope-auditor always.

amendments:
- During implementation, `test_remove_from_saved_only_removes_that_card` (the two-cards-saved,
  remove-one-scoped test) hit a `KeyError` on the second of two different-card focus-then-save
  cycles. Isolated the exact trigger empirically (single-card focus+save is fine regardless of
  how many runs follow; two DIFFERENT cards' focus+save cycles is what triggers it). Test fixed
  by seeding both "save" interactions directly onto `session_state` (matching
  `append_interaction`'s exact row shape) instead of driving both saves through Discover's UI,
  while still exercising the actual thing under test -- "Remove from saved" scoping -- through
  real Saved-tab UI clicks, unstubbed. No production file touched or needed changing.

  What this crash actually is, corrected after cto-reviewer's round-1 finding (see below): an
  initial pass here claimed, after one manual browser test, that this was "confirmed... not a
  production bug." That was overclaimed. cto-reviewer traced the real mechanism: `AppTest`'s
  `LocalScriptRunner` subclasses Streamlit's own production `ScriptRunner` unmodified, and the
  cleanup path that raises this `KeyError` (`session_state.py`'s `_compact_state`) is real,
  shared production code -- which itself wraps this exact case in `except KeyError: pass`,
  citing a known upstream Streamlit issue (`streamlit/issues/7206`) about stale widget
  metadata. The underlying condition (viewing two different cards' metric-playground panels
  swaps the full active widget-key set) is real and not AppTest-specific; what IS AppTest-
  specific is that `element_tree.py`'s `get_widget_states()` reads widget state without
  production's own defensive swallowing, turning a condition production silently tolerates
  into a hard test failure. One manual pass not reproducing a visible crash is consistent with
  this (production swallows it) but doesn't rule out a rarer or timing-sensitive path still
  causing a real problem. Corrected the test's own docstring to state this accurately instead
  of the overclaimed version. Flagging to the owner as a genuinely open question, not a closed
  one -- worth a tracked follow-up if it's worth someone's time, not something to silently drop
  or unilaterally file an issue for.
- Mutation-tested the scoping assertion for real: changed `saved_remove_current`'s handler to
  call `clear_interactions()` instead of `append_interaction(selected, "unsave")`, confirmed
  the test fails with the exact predicted symptom (`assert None is not None` on the BETA row
  check -- both cards wiped instead of just the selected one), restored `frontend/app.py` from
  a backup, confirmed `git diff --stat frontend/app.py` shows zero diff (untouched, as
  scope_paths requires) and the full suite (536 tests) passes again.
- scope-auditor (round 1) FAILED: this contract's objective originally claimed
  `git log --all -S"AppTest"` returns "zero hits, ever," carried over unverified from an
  earlier exploration pass in this session rather than re-checked before being asserted here.
  False -- 5 real commits, two of which (`702bfb62`, `0bb8997c`) explicitly discuss AppTest.
  Corrected above, in the objective, with the real history and why it doesn't conflict with
  this task. Same disclosure-accuracy class as item 3's MR !101 mis-citation.
- cto-reviewer (round 1) FAILED: the "not a production bug" overclaim above. Also flagged,
  separately, that they accidentally edited `frontend/app.py` while independently re-verifying
  the mutation-test claim, self-caught it, reverted, and confirmed clean -- verified
  independently here too (`git status`/`git diff HEAD --stat` after their round showed exactly
  the 4 expected files, `frontend/app.py` not among them).
- cto-reviewer (round 2) FAILED: the round-1 fix itself introduced a new, unverified mechanism
  claim -- the test docstring's corrected version stated `_compact_state` is "called from the
  same `ScriptRunner.on_script_finished` that `LocalScriptRunner` subclasses unmodified." Wrong
  on both parts, per cto-reviewer's direct source trace: `_compact_state` is only called from
  `SessionState.on_script_will_rerun` (not `on_script_finished`, a different method entirely),
  and `LocalScriptRunner` DOES override `_on_script_finished` with its own copy -- the method
  it actually inherits unmodified (`ScriptRunner._run_script`, which calls
  `on_script_will_rerun`) was never named. The same defect class round 1 caught (an asserted
  mechanism not traced against source), relocated into the fix meant to correct it.
  Independently re-verified against the installed Streamlit 1.57.0 source myself (grepped
  `_compact_state`/`on_script_will_rerun`/`_on_script_finished` across `session_state.py`,
  `script_runner.py`, `local_script_runner.py`; confirmed `_run_script` is absent from
  `LocalScriptRunner`'s override list, so it is inherited unmodified). Corrected the docstring
  to the verified chain: `_compact_state` <- `SessionState.on_script_will_rerun` <-
  `ScriptRunner._run_script` (not overridden by `LocalScriptRunner`). `contract.md`'s own
  amendments were not affected -- cto-reviewer confirmed this file already used the same
  general, defensible phrasing as their round-1 finding, not the specific wrong claim.
- All three fixes re-verified together: full suite re-run (536 passed), em/en-dash re-scanned on
  the diff against HEAD (0 hits), `git status` confirms scope_paths still exactly matched.
