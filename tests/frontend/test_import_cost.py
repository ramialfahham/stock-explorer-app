"""The app's cold start is dominated by imports on Render's box; heavy modules that only one
screen needs must not load with the app. Run in a subprocess because the test session itself
imports them elsewhere."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]


def _modules_after_importing_app() -> set[str]:
    code = (
        "import sys; sys.path.insert(0, 'frontend'); import app; "
        "print(chr(10).join(sorted(sys.modules)))"
    )
    out = subprocess.run(
        [sys.executable, "-c", code], cwd=str(REPO), capture_output=True, text=True, check=True
    )
    return set(out.stdout.split())


def test_importing_the_app_does_not_load_yfinance_or_pandas() -> None:
    loaded = _modules_after_importing_app()
    assert "app" in loaded
    for heavy in ("yfinance", "pandas", "numpy"):
        assert heavy not in loaded, f"{heavy} loads with the app; only Saved news needs it"
