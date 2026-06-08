# Streamlit Community Cloud — Stock Swipe

Deploy the discovery UI (`frontend/app.py`) against Supabase data exported by the data pipeline.

## Prerequisites

1. **Data pipeline green** — `mart_stock_cards` populated in Supabase ([`operations_guide.md`](operations_guide.md)).

## Deploy steps

1. Go to [share.streamlit.io](https://share.streamlit.io) → **Create app** → connect this GitHub repo.
2. **Main file path:** `frontend/app.py` (existing apps) or `streamlit_app.py` (new apps). Streamlit Cloud **does not allow changing** the main file after create — pick once at deploy time.
3. **Python version:** 3.11 (repo includes `.python-version`; Cloud may default to 3.14 otherwise)
4. **Requirements file:**
   - Main file `frontend/app.py` → `frontend/requirements.txt`
   - Main file `streamlit_app.py` (repo root) → **`requirements.txt` at repo root** (must include `streamlit-extras`; root file is kept in sync for this path)
   - Or override in App settings → Advanced settings → Requirements file → `frontend/requirements.txt` for either entrypoint
5. **Secrets** — App settings → Secrets, TOML format from [`.streamlit/secrets.toml.example`](../.streamlit/secrets.toml.example):
   - `SUPABASE_URL`
   - `SUPABASE_ANON_KEY` (anon / publishable key only — never the service role key)
6. Deploy. Open the app URL — Discover and Search load immediately (no login). Save/skip persist in browser localStorage on the device.

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
