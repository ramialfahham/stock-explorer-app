# Streamlit Community Cloud — Stock Swipe

Deploy the discovery UI (`frontend/app.py`) against Supabase data exported by the data pipeline.

## Prerequisites

1. **Data pipeline green** — `mart_stock_cards` populated in Supabase ([`operations_guide.md`](operations_guide.md)).
2. **Supabase Auth** — Email provider enabled ([`supabase_setup.md`](supabase_setup.md) §5–6).

## Deploy steps

1. Go to [share.streamlit.io](https://share.streamlit.io) → **Create app** → connect this GitHub repo.
2. **Main file path:** `streamlit_app.py` (repo root — avoids import issues with `frontend/app.py`)
3. **Python version:** 3.11
4. **Requirements file:** `frontend/requirements.txt` (keeps install fast; omit dbt/ingestion deps)
5. **Secrets** — App settings → Secrets, TOML format from [`.streamlit/secrets.toml.example`](../.streamlit/secrets.toml.example):
   - `SUPABASE_URL`
   - `SUPABASE_ANON_KEY` (anon / publishable key only — never the service role key)
6. Deploy. Open the app URL and sign in (or create a test user in Supabase Auth).

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
