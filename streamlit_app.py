"""Streamlit Community Cloud entrypoint (repo root)."""

import importlib.util
import sys
from pathlib import Path

# #region agent log
def _debug_log(message: str, data: dict, hypothesis_id: str = "H1") -> None:
    import json
    import time

    payload = {
        "sessionId": "669620",
        "runId": "post-fix",
        "hypothesisId": hypothesis_id,
        "location": "streamlit_app.py",
        "message": message,
        "data": data,
        "timestamp": int(time.time() * 1000),
    }
    try:
        log_path = Path(__file__).resolve().parent / "debug-669620.log"
        with log_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload) + "\n")
    except OSError:
        pass


_debug_log(
    "entrypoint startup",
    {
        "entry": str(Path(__file__).resolve()),
        "streamlit_extras_installed": importlib.util.find_spec("streamlit_extras") is not None,
    },
)
# #endregion

sys.path.insert(0, str(Path(__file__).resolve().parent / "frontend"))

import app

# #region agent log
_debug_log("app module imported", {"ok": True}, hypothesis_id="H5")
# #endregion

app.main()
