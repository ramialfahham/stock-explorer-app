# Task contract
> DISPOSABLE. **Owns:** THIS task's objective, `scope_paths`, reserved decisions and
> `done_when`.
> **Never:** anything that outlives the task. Overwritten by the next task.

objective: The live site's 2.8 s from script start to first element, named with the
  `?timing=1` probe: our script runs in 26 to 102 ms warm; the gap is Streamlit's source
  watcher, which after every new session scans every loaded module on the thread that
  flushes messages to the browser (`LocalSourcesWatcher.update_watched_modules`, 3.0 s on
  this machine for 2,097 modules). Turn the watcher off in production.

scope_paths:
  - render.yaml
  - docs/streamlit_deploy.md
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/active_work.md

decisions_reserved:
  - Production only, via the Render start command (`--server.fileWatcherType none`); the
    local launcher keeps live reload. The watcher serves editing; nothing changes on disk on
    Render. No cost, no dependency, one flag on an existing command; the why sits beside it.

done_when:
  - `render.yaml`'s startCommand carries the flag; the file parses; the quoted command in
    `docs/streamlit_deploy.md` matches it.
  - Proven locally before the change: same server, same browser probe, full list at 4.5 to
    5.4 s with the watcher, 1.4 s without. Live numbers after the deploy go in the handover.

impact_map: Deployed process only. Local dev unchanged.
