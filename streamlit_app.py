"""Deployed-app entrypoint (repo root) — see render.yaml's startCommand."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "frontend"))

import timing

timing.entry_started()

import app

app.main()
