# Review

> DISPOSABLE. **Owns:** THIS task's reviewer verdicts and the staged-diff hash they were
> given against.
> **Never:** a rule. Overwritten by the next task.

diff_sha256: 39c222b8e1b1c1e0a217214c6c32b3d6d13a8cace2b585c1702a44b194e283a9

One reviewer, by routing: scope-auditor (`always`; `render.yaml` and `docs/*` route nowhere
else). Two rounds.

## What shipped

`--server.fileWatcherType none` on the Render start command, with the why beside it: after
every new session Streamlit's source watcher scans every loaded module on the thread that
flushes messages to the browser, about 3 s during which nothing paints. Proven locally: same
server, full list at 4.5 to 5.4 s with the watcher, 1.4 s without. The deploy doc's quoted
build and start commands match render.yaml again.

## Round 1

scope-auditor confirmed the three claims in the comment against Streamlit's source
(`app_session.py` runs `update_watched_modules` on the event loop after each run; it walks
`sys.modules` on a new session's first run; `none` skips creating the watcher) and found
`docs/streamlit_deploy.md` quoting the old start command; the build command on the same
line had been stale since !140. Both fixed.

## scope-auditor

VERDICT: PASS

## Owner decisions

None: a flag on an existing command, production only.
