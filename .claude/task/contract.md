# Task contract

objective: Scope the Discover list performance problem as its own backlog item, per the owner's
  request. Found while investigating a report that tapping a list row to open its card visibly
  hangs. This task lays out what's confirmed by direct measurement, a code-grounded but not yet
  empirically confirmed mechanism for a related symptom, and the open questions that block
  writing a build contract. It does not choose a fix: a widget-count reduction (pagination or
  an alternative) is a user-facing change (page size, pagination UI shape) reserved to the
  owner under this repo's working agreement §6, not something this task decides.

scope_paths:
  - docs/backlog/discover_list_performance.md
  - .claude/active_work.md
  - .claude/task/contract.md
  - .claude/task/review.md

decisions_reserved:
  - Everything in `docs/backlog/discover_list_performance.md`'s "Open questions" section:
    whether a widget-count fix (pagination or an alternative) is the direction, what shape it
    takes, page size, whether the `st.rerun()`-mid-loop hypothesis needs its own profiling spike
    before or independent of a widget-count fix, whether this interacts with the already-decided
    "first-time Discover default" scope, and whether Saved needs the same treatment. None of
    these are answered by this task; they are the owner's call before a build contract can be
    written.
  - Which, if any, of the four candidate directions sketched in the doc is worth pursuing, or
    whether none of them are. Presented as discussion starters with honest tradeoffs, not a
    recommendation ranked or defaulted to inside the doc itself (a working recommendation is
    recorded separately in `.claude/active_work.md`, labeled explicitly as not yet approved,
    matching how this session has handled other scoping tasks).
  - **Found by round-1 scope-auditor review, a minor, non-blocking mis-attribution.** The
    "ruled out" paragraph credited the list's sort step to `explore_filters.filter_pool`; the
    sort is actually a separate `pool.sort(...)` call in `app._discover_pool`, right after
    `filter_pool` returns. Doesn't change the "no nested loop, not a performance concern"
    conclusion, but the doc should name the function that actually does the thing. Fixed.

done_when:
  - `docs/backlog/discover_list_performance.md` exists, separates confirmed measurements (widget
    count, DOM node count, click-registration timing at two list sizes) from the
    not-yet-empirically-confirmed `st.rerun()`-mid-loop hypothesis for the second symptom, states
    plainly what was ruled out and how (reading the code, not guessing), and lists open questions
    and candidate directions without resolving any of them.
  - `.claude/active_work.md`'s existing note about this problem (left by the immediately-prior
    verdict-dot task, describing it as "not yet scoped") is replaced with a pointer to the new
    doc and the new `st.rerun()` finding, not left as stale, superseded prose.
  - No code, test, CI, or dependency file touched: documentation and scoping only.
  - No em dash or en dash on any added line.

impact_map:
  - Documentation only. No frontend, dbt, ingestion, or CI behavior changes.
  - Sets up (but does not start) a future task that will need a task contract of its own once
    the owner answers the open questions above.

amendments: (none)
