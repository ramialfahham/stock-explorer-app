# Task contract
> DISPOSABLE. **Owns:** THIS task's objective, `scope_paths`, reserved decisions and
> `done_when`.
> **Never:** anything that outlives the task. Overwritten by the next task.

objective: The app shows a black screen for seconds on every load (owner, 2026-09-14: not
  acceptable; zero spend). Three causes measured, three fixes: paint the header before
  anything that waits; a splash in Streamlit's own index.html so the first byte shows the
  product; the saved list moves from the streamlit_extras localStorage component (a
  components-v2 widget that stalls rendering and forces a second run on every load) to a
  cookie Streamlit reads on the first run.

scope_paths:
  - frontend/app.py
  - frontend/browser_storage.py
  - frontend/styles.py
  - frontend/requirements.txt
  - scripts/patch_streamlit_splash.py
  - render.yaml
  - .streamlit/config.toml
  - tests/frontend/test_browser_storage.py
  - tests/frontend/test_app_e2e.py
  - tests/tooling/test_patch_streamlit_splash.py
  - README.md
  - docs/north_star.md
  - docs/streamlit_deploy.md
  - tests/README.md
  - docs/supabase_setup.md
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/active_work.md

decisions_reserved:
  - Cookies over a lighter localStorage component: owner, in chat (A over B), zero spend, no
    new dependency; streamlit-extras removed from the frontend requirements.
  - What persists changes from the event log to the current state: saved keys with their
    save time. Skips were never read by any screen (saved_keys_with_order ignores them), so
    nothing user-visible changes; a full event history is no longer kept anywhere.
  - Migration: a first visit with no cookie and a saved list in localStorage from the old
    storage writes the cookie and reloads once. Not asked; recorded so nobody's saved list
    silently vanishes. Delete on the owner's word.
  - Two user-visible strings are new and the owner's to reword (§6): "Loading cards" under
    the header while the deck is fetched, and the splash "Stock Explorer" / "Loading" in
    Streamlit's index.html before its JavaScript arrives. Both use the existing brand
    colours; the splash colours are literal in the patch script because it runs before the
    app can be imported.
  - Streamlit usage telemetry off (`browser.gatherUsageStats = false`): four requests to a
    third-party webhook per load, one of them the slowest request on the live site; no
    effect on the app.
  - Deploy-time patching of Streamlit's index.html is a NEW build step in render.yaml (§6,
    new mechanism). It was put to the owner in chat as step 2 of the plan ("a build step on
    Render patches it to show 'Stock Explorer, loading' at first byte") before the owner's
    "Now solve it"; recorded here so the owner can strike it. Idempotent, exits 1 without
    writing if a Streamlit upgrade changes the file's shape, and a test checks the installed
    Streamlit still has that shape.

done_when:
  - `main()` renders the brand header before the storage read and the deck fetch; a
    "Loading cards" line shows while the deck is fetched and clears after.
  - `scripts/patch_streamlit_splash.py` writes the splash into `<div id="root">` once,
    refuses an unrecognised file, `--check` reports state; render.yaml runs it after pip.
  - `browser_storage.py` reads `st.context.cookies` on the first run, writes numbered
    cookies through a components.html script only in a run that saved or cleared, migrates
    a legacy localStorage list once. Tests cover encode/decode round trips incl. chunking,
    load-once, save/unsave/clear queueing, flush rendering once, migration gating.
  - A crafted cookie never raises out of the first run: epochs are capped at ten digits,
    `_iso` skips a value the platform cannot convert, an e2e test proves a save's cookie
    script is rendered by the run after the save (removing `flush_storage_writes()` fails
    it), and the write script cannot be closed early by a "</" in a value.
  - The migration writes cookies in `COOKIE_CHUNK_BYTES` chunks and removes the localStorage
    copy only after the browser reports the first cookie present; a browser that refuses
    cookies keeps its list and does not reload.
  - Live check in a browser on the local server: a save writes `ss_saved_0`, a fresh
    session reads it back ("1 saved", the card excluded from Discover), no iframe on a plain
    load.
  - `pytest tests/ -q` green; the five docs that said localStorage say cookie.

impact_map: Card-level UX only; no dbt, export or data change. The deployed build gains one
  step. Users with a saved list in localStorage get it migrated on their next visit.
