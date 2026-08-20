# Task contract

objective: **Render deploy path.** Add a committed `render.yaml` Blueprint plus doc/comment
  updates so the app can deploy from GitLab via Render, replacing the dead Streamlit Community
  Cloud path (GitHub-only, and the GitHub account is suspended indefinitely). Owner chose
  Render over Fly.io and self-hosting on Hetzner. Approved plan:
  ~/.claude/plans/pure-juggling-frost.md.

scope_paths:
  - render.yaml                       # new
  - docs/streamlit_deploy.md          # rewrite deploy-steps section, keep Local dev as-is
  - docs/supabase_setup.md            # retitle + rewrite §5
  - CLAUDE.md                         # 1-line stack swap
  - docs/project_context.md           # 1-line stack table swap
  - frontend/requirements.txt         # 1-line header comment reword
  - streamlit_app.py                  # 1-line docstring reword
  - .streamlit/secrets.toml.example   # 1-line comment clarify (local-dev-only now)
  - tests/tooling/test_ci_reachability.py   # comment-only, no assertion change
  - .claude/active_work.md            # record the Render decision + this change's state
  - .claude/task/contract.md

decisions_reserved (owner-approved this session):
  - **Render chosen** over Fly.io (CLI-driven, no native git integration) and self-hosting on
    the existing Hetzner box (most control, most ongoing maintenance) — native GitLab OAuth
    integration with auto-deploy on push, closest match to what Streamlit Community Cloud
    offered.
  - **README.md deliberately NOT touched in this diff** (lines 11/13/92 — demo URL, "sleeps
    when idle" blurb, stack table) — depends on the live `*.onrender.com` URL, which doesn't
    exist until the owner completes the manual dashboard steps below. Bundle those three edits
    together once the URL is known; editing the stack-table wording now while the URL still
    points at the dead `.streamlit.app` domain would be actively misleading.
  - **`docs/product_roadmap_2026-06.md`'s "Manual smoke on Streamlit Cloud after merge" line
    NOT touched** — a dated historical roadmap snapshot; the actually-enforced checklist today
    is `docs/working_agreement.md`'s UX PR gate, which doesn't mention Streamlit Cloud. Flagged
    to the owner, not silently rewritten.
  - **I (the agent) cannot perform the account/OAuth/secrets steps** — creating the Render
    account, authorizing GitLab OAuth, and entering `SUPABASE_URL`/`SUPABASE_ANON_KEY` into
    Render's dashboard are all owner-only manual steps, listed in the plan and repeated in
    `docs/streamlit_deploy.md`. This diff only prepares the repo so those steps are minimal.

technical_definition:
  - `render.yaml` (repo root): `services: [{type: web, runtime: python, plan: free,
    branch: main, buildCommand: pip install -r frontend/requirements.txt, startCommand:
    streamlit run streamlit_app.py --server.port $PORT --server.address 0.0.0.0, envVars:
    [{key: SUPABASE_URL, sync: false}, {key: SUPABASE_ANON_KEY, sync: false}]}]`. `runtime`
    (not the deprecated `env`) is Render's current Blueprint schema key, verified against
    Render's live docs during planning. `buildCommand` uses `frontend/requirements.txt` only —
    not root `requirements.txt`, which pulls in the whole dbt/analytics stack unnecessarily
    (Render's `buildCommand` is a free-form shell command, unlike Streamlit Cloud's
    requirements-file-tied-to-main-file convention). No `PYTHON_VERSION` env var — Render
    auto-reads the existing root `.python-version` (3.11).
  - No code changes needed anywhere: `frontend/settings.py`'s `get_supabase_url()`/
    `get_supabase_anon_key()` already fall back from `st.secrets` (wrapped in try/except) to
    plain `os.environ.get(...)`, which is exactly what Render's plain env vars need.
    `streamlit_app.py`'s `sys.path` + `import app; app.main()` entrypoint is host-agnostic —
    unchanged behavior, only its docstring comment is reworded.

explicitly_not_in_scope:
  - README.md's demo-URL/stack-table lines (see decisions_reserved above).
  - docs/product_roadmap_2026-06.md's dated Streamlit-Cloud-smoke line (see above).
  - Archived handover docs (`docs/handover_2026-08-18.md`, `docs/handover_2026-05-24.md`) —
    point-in-time records per this repo's own convention, left alone.
  - Any actual Render account creation, GitLab OAuth authorization, or secret entry — owner-
    only, cannot be performed by the agent (credential/account-creation actions).

done_when:
  - `render.yaml` exists, is well-formed YAML, and matches the schema above.
  - No live (non-archived, non-`.venv`) file still says "Streamlit Community Cloud" or
    "share.streamlit.io" except the three deliberately-deferred `README.md` lines and the
    historical docs named in `explicitly_not_in_scope`.
  - `pytest tests/tooling/test_ci_reachability.py` still passes (comment-only change).
  - scope-auditor (always) + cto-reviewer (`tests/*`) both PASS on the final staged diff, per
    `.claude/review_routing.json`.
  - Owner has the exact manual dashboard steps needed to go live, handed back clearly — real
    end-to-end verification (the app actually live on Render) happens only after the owner
    completes those steps and reports the URL back; this diff does not claim that's done.

impact_map:
  - Docs/config-only change (new `render.yaml`, doc rewrites, comment rewords). No dbt/
    ingestion/Supabase-schema change, no frontend behavior change. Required reviewers (per
    `.claude/review_routing.json`): **scope-auditor** (always) · **cto-reviewer**
    (`tests/*` — the `test_ci_reachability.py` comment edit routes there even though it's
    non-behavioral). Neither analytics-engineer nor data-engineer nor equity-analyst-reviewer
    route to this diff.

amendments:
  - **Service name (owner-approved this session):** the round-1 scope-auditor review flagged
    that `render.yaml`'s `name: stock-swipe-app` sets the default public subdomain
    (`*.onrender.com`) once deployed — a public identifier under §6, needing explicit owner
    sign-off even though it looked like an obvious default (matches the repo name). Escalated;
    owner chose `stock-explorer-app` instead (matches the product name — see `north_star.md`:
    "Product name: Stock Explorer... Repo name may remain stock-swipe-app"). `render.yaml`
    updated accordingly.
