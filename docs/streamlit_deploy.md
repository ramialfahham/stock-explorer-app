# Streamlit on Render -- Stock Explorer

Deploy the discovery UI (`frontend/app.py`, via the `streamlit_app.py` entrypoint) against
Supabase data exported by the data pipeline.

## Prerequisites

1. **Data pipeline green** — `mart_stock_cards` populated in Supabase ([`operations_guide.md`](operations_guide.md)).

## Deploy steps

The service definition is committed as [`render.yaml`](../render.yaml) (a Render Blueprint) —
Render auto-detects it, so most fields below are already set in the repo. Only the account
connection and the two secrets need a human.

1. Sign up / log in at [render.com](https://render.com).
2. **Connect GitLab** — Account Settings → Connected Accounts → GitLab OAuth, authorize access
   to `rami.al-fahham/stock-explorer-app`.
3. **New → Blueprint** → select the repo. Render reads `render.yaml`: Python runtime,
   `.python-version` (3.11), build command (`pip install -r frontend/requirements.txt && python scripts/patch_streamlit_splash.py`), start
   command (`streamlit run streamlit_app.py --server.port $PORT --server.address 0.0.0.0 --server.fileWatcherType none`), free
   plan, auto-deploy on every push to `main`.
4. **Secrets** — Render prompts for the two `sync: false` env vars declared in `render.yaml`,
   same values as [`.streamlit/secrets.toml.example`](../.streamlit/secrets.toml.example):
   - `SUPABASE_URL`
   - `SUPABASE_ANON_KEY` (anon / publishable key only — never the service role key)
5. Confirm branch `main`, click **Apply/Create**. First deploy runs automatically. Open the
   assigned `*.onrender.com` URL -- Discover loads immediately (no login). Save/skip
   persist in a browser cookie on the device.

Free-tier instances spin down after ~15 minutes idle; the next visit takes 30-60s to cold-start.

## Local dev

From repo root:

```bash
pip install -r frontend/requirements.txt
cp .streamlit/secrets.toml.example .streamlit/secrets.toml   # fill values
streamlit run streamlit_app.py
```

Or use `.env` with `SUPABASE_URL` and `SUPABASE_ANON_KEY` (see `.env.example`).

## UX notes

Card layout follows [`north_star.md`](north_star.md): three headline metrics on the card;
net debt / EBITDA and FCF margin under **More metrics (scroll)**.

Save and skip are stored in the browser only (not synced across devices). Supabase accounts are deferred to a later release; the `user_interactions` table remains for that phase.
