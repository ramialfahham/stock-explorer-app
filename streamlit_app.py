"""Streamlit Community Cloud entrypoint (repo root)."""

import sys
from pathlib import Path

try:
    import streamlit_extras  # noqa: F401 — required by browser_storage
except ImportError as exc:
    raise ImportError(
        "Missing streamlit-extras. Install frontend deps: "
        "pip install -r frontend/requirements.txt — "
        "or on Streamlit Cloud set Requirements file to frontend/requirements.txt "
        "(root streamlit_app.py uses repo requirements.txt)."
    ) from exc

sys.path.insert(0, str(Path(__file__).resolve().parent / "frontend"))

import app

app.main()
