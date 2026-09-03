# Task contract

objective: Run the full Discover/Saved/Search user-flow simulation the owner requested
  2026-08-31 ("find further UX inconsistencies beyond the ones already found and fixed") and log
  the findings to the backlog. Investigation only -- no fixes chosen or shipped in this task; the
  owner directed "log them to the backlog" after reviewing a summary of what was found.

  Method: started the local dev server and drove the app by hand (Browser pane), not just read
  from code, across all three tabs -- Search's query/result/focus mechanics, Saved at volume (17
  saved companies) including the destructive "Clear saved" action, and Discover's market/sector
  filter across tab navigation. Four bugs confirmed reproducible by direct interaction; one
  code-visible structural risk (Saved has no pagination, same class MR !70 fixed for Discover)
  could not be confirmed as a felt problem at the volume tested and is recorded as unconfirmed,
  not asserted as a live issue.

scope_paths:
  - docs/backlog/discover_saved_search_ux_findings.md (new file)
  - .claude/active_work.md
  - .claude/task/contract.md
  - .claude/task/review.md

decisions_reserved: none for this task -- it only records findings, matching
  `docs/backlog/discover_list_performance.md`'s own precedent of separating "what was confirmed"
  from "what the owner should decide," without picking a fix direction. Every open question this
  investigation raised (fix direction for each bug, whether "Clear saved" needs a confirmation
  step, whether to build Saved pagination proactively) is recorded as an explicit open question
  in the new doc for the owner to answer later, not decided here.

done_when:
  - `docs/backlog/discover_saved_search_ux_findings.md` created, following
    `discover_list_performance.md`'s established template (Status / Summary / Context
    confirmed-vs-hypothesis / Open questions / Candidate directions / Related).
  - Every claimed bug cites the exact file/line(s) responsible, verified by direct code read,
    not asserted from memory of the live-testing session alone.
  - The Discover-filter-reset finding is recorded honestly as "behavior confirmed, mechanism not
    yet confirmed" -- the file/line investigation ruled out the same-shaped explanation that fit
    the Search-box bug (missing widget `key=`) rather than reusing it without checking, since the
    filter selectboxes turned out to already have explicit keys.
  - `.claude/active_work.md`'s open-items list updated: the "never done" simulation item replaced
    with a short pointer to the new doc's findings, and the backlog-doc-count line updated to
    include it.
  - No em dash or en dash on any added line.
  - `pytest`/`dbt build` untouched by this task (no code changed) -- not re-run.

impact_map:
  - Pure documentation addition. No `frontend/`, `dbt_analytics/`, `scripts/`, or `supabase/`
    file touched -- nothing in this task changes app behavior, test coverage, or CI.
  - Sets up (but does not itself decide) up to 3 follow-up tasks: the navigation-state-loss
    fix(es), a possible "Clear saved" confirmation step, and a possible Saved-pagination fix --
    each its own future task contract with its own `decisions_reserved` once the owner picks a
    direction.

amendments: none.
