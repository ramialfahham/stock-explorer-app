"""Shared pytest path setup for the whole suite.

Tests import repo code three ways: ``ingestion`` as a package (``ingestion.yfinance.*``),
and ``frontend`` / ``scripts`` modules directly (``import card_copy``,
``from check_export_health import ...``). Putting the repo root plus ``frontend/`` and
``scripts/`` on ``sys.path`` once, here, lets every test — in any ``tests/`` subdir —
import without hand-rolling ``sys.path`` per file.
"""

from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
for _entry in (_REPO_ROOT, _REPO_ROOT / "frontend", _REPO_ROOT / "scripts"):
    _path = str(_entry)
    if _path not in sys.path:
        sys.path.insert(0, _path)
