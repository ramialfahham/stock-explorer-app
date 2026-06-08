"""Debug probe: reproduce Streamlit Cloud import chain with NDJSON logging."""

from __future__ import annotations

import importlib
import json
import sys
import time
import traceback
from pathlib import Path

LOG_PATH = Path(__file__).resolve().parents[1] / "debug-669620.log"
SESSION_ID = "669620"
RUN_ID = "pre-fix"


def _log(hypothesis_id: str, location: str, message: str, data: dict) -> None:
    # #region agent log
    payload = {
        "sessionId": SESSION_ID,
        "runId": RUN_ID,
        "hypothesisId": hypothesis_id,
        "location": location,
        "message": message,
        "data": data,
        "timestamp": int(time.time() * 1000),
    }
    with LOG_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload) + "\n")
    # #endregion


def _try_import(module: str, hypothesis_id: str) -> bool:
    try:
        importlib.import_module(module)
        _log(hypothesis_id, "debug_streamlit_import.py", f"import ok: {module}", {"module": module})
        return True
    except Exception as exc:  # noqa: BLE001
        _log(
            hypothesis_id,
            "debug_streamlit_import.py",
            f"import failed: {module}",
            {
                "module": module,
                "exc_type": type(exc).__name__,
                "exc_msg": str(exc),
                "traceback_tail": traceback.format_exc().splitlines()[-4:],
            },
        )
        return False


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    frontend = repo_root / "frontend"
    sys.path.insert(0, str(frontend))

    _log("H3", "debug_streamlit_import.py", "startup paths", {
        "cwd": str(Path.cwd()),
        "repo_root": str(repo_root),
        "frontend_in_syspath": str(frontend) in sys.path,
        "streamlit_extras_installed": importlib.util.find_spec("streamlit_extras") is not None,
    })

    # H1: streamlit_extras missing breaks browser_storage
    if not _try_import("streamlit_extras", "H1"):
        _log("H1", "debug_streamlit_import.py", "H1 confirmed path", {"blocked_at": "streamlit_extras"})

    if not _try_import("browser_storage", "H1"):
        return 1

    # H2: app imports request_landing from browser_storage
    try:
        from browser_storage import request_landing  # noqa: F401

        _log("H2", "debug_streamlit_import.py", "request_landing import ok", {"has_callable": callable(request_landing)})
    except Exception as exc:  # noqa: BLE001
        _log("H2", "debug_streamlit_import.py", "request_landing import failed", {
            "exc_type": type(exc).__name__,
            "exc_msg": str(exc),
        })
        return 1

    # H5: same top-level imports as app.py (do not import app — it runs main())
    import_statements = [
        ("explore_filters", "H5"),
        ("landing", "H5"),
    ]
    for mod, hid in import_statements:
        if not _try_import(mod, hid):
            return 1

    _log("H5", "debug_streamlit_import.py", "import chain ok", {"status": "success"})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
