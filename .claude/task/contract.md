# Task contract
> DISPOSABLE. **Owns:** THIS task's objective, `scope_paths`, reserved decisions and
> `done_when`.
> **Never:** anything that outlives the task. Overwritten by the next task.

objective: On the live site a return visit spends 2.1 s between Streamlit's JavaScript being
  ready and the script starting, and 2.8 s between the script starting and its first
  element, the header; locally both gaps are under 0.3 s. Render's logs are not readable
  from here. `?timing=1` makes the page print its own stage clock so the gap can be named.

scope_paths:
  - frontend/timing.py
  - frontend/app.py
  - streamlit_app.py
  - tests/frontend/test_timing.py
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/active_work.md

decisions_reserved:
  - A diagnostic switch in production, visible to anyone who adds `?timing=1`: one caption
    line of millisecond gaps and the process age, no data. Owner said go in chat to this
    exact proposal; remove or keep after the measurement is the owner's call.

done_when:
  - `streamlit_app.py` marks when the entry script starts (before `import app`);
    `app.main()` marks css, header, cookies, deck, page; the caption renders only with the
    flag. Unit test over the report and the flag gate; live check locally: the caption shows
    with the flag and not without.
  - `pytest tests/ -q` green.

impact_map: Frontend only; a few perf_counter calls per run without the flag.
