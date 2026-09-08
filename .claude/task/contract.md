# Task contract

objective: Record the two UptimeRobot keep-alive monitors and the corrected pipeline-failure
  email route in `docs/operations_guide.md`, and close open item 6 in the handover.

  Documentation only. Both changes were made by the owner in the UptimeRobot and GitLab UIs
  during this session; this task writes down what exists so a future session can verify and
  maintain it. Nothing here was previously recorded in the repo.

  Two findings this captures, neither obvious from reading either system alone:

  1. The pre-existing app monitor (`stock-explorer-app.onrender.com`) never kept the DATABASE
     awake. A plain HTTP request to a Streamlit app returns the static page shell only --
     Streamlit runs the app script, and therefore any Supabase query, on websocket connect,
     not on GET. Verified 2026-09-08: the response body contains no card data. Until a second
     monitor pointed at the Supabase REST API was added, the database was uncovered and
     survived only on real visits.
  2. `docs/operations_guide.md` has documented the GitLab "Pipeline emails" project
     integration as the alerting route since MR !101. That integration is not in this
     project's Settings -> Integrations list, and the API returns `404 Integration Not Found`
     for `pipelines-email`. The route that works is GitLab's built-in per-user notification
     setting (bell -> Custom -> Failed pipeline). The documented step was never verified when
     it was written; it was recorded as a pending owner action and left unchecked.

scope_paths:
  - docs/operations_guide.md
  - .claude/active_work.md
  - .claude/task/contract.md
  - .claude/task/review.md

decisions_reserved:
  - Whether to keep relying on a per-user notification (emails the account that set it) rather
    than a recipient list. Fine for a solo project; a second maintainer would have to set
    their own. Not changed here.
  - The dead-man's-switch gap is unchanged and still open: nothing alerts if the scheduled
    pipeline never fires at all, because there is no failed run to notify from.

done_when:
  - `docs/operations_guide.md` states both monitors, what each one covers, and explicitly why
    the app monitor does not cover the database.
  - The `sb_publishable_` vs `sb_secret_` distinction is stated, since the database monitor
    URL carries a key as a query parameter.
  - The stale "Pipeline emails" integration instruction is replaced with the route that
    actually works, and says plainly that the old one was never verified.
  - Open item 6 in `.claude/active_work.md` is closed with the trap preserved.
  - `.claude/active_work.md` stays under its 32,000-byte injection cap.

impact_map: Documentation only. No code, no dbt model, no schema, no CI. Nothing downstream
  reads these files.

amendments:
  - (none)
