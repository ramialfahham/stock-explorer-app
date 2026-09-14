#!/usr/bin/env python3
"""Put a splash into Streamlit's own index.html so the first byte shows the product, not black.

Streamlit serves a static index.html whose <div id="root"> is empty until its JavaScript
bundle (dozens of files) has downloaded and React has mounted; on a small host that is
seconds of a blank dark page. This runs once at deploy time, after pip install (see
render.yaml's buildCommand), and writes brand-coloured "loading" markup into that div. React
replaces the div's children on mount, so the splash disappears the moment the real app can
draw. Idempotent: a second run finds the marker and leaves the file alone.

    python scripts/patch_streamlit_splash.py            # patch the installed Streamlit
    python scripts/patch_streamlit_splash.py --check    # exit 1 if not patched
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

MARKER = "ss-splash"
ROOT_DIV = '<div id="root"></div>'

# Colours mirror .streamlit/config.toml and frontend/styles.py; kept literal here because this
# file runs before the app and must not import it.
SPLASH = (
    '<div id="root">'
    f'<div class="{MARKER}" style="min-height:100vh;display:flex;flex-direction:column;'
    "align-items:center;justify-content:center;background:#0a0a0b;color:#f4f4f5;"
    'font-family:sans-serif;">'
    '<div style="font-size:1.375rem;font-weight:600;color:#c9a962;">Stock Explorer</div>'
    '<div style="margin-top:0.5rem;font-size:0.875rem;color:#94949e;">Loading</div>'
    "</div></div>"
)


def index_html_path() -> Path:
    import streamlit  # noqa: PLC0415

    return Path(streamlit.__file__).resolve().parent / "static" / "index.html"


def patch(text: str) -> str:
    """The patched document; unchanged when already patched or when the root div is absent."""
    if MARKER in text or ROOT_DIV not in text:
        return text
    return text.replace(ROOT_DIV, SPLASH, 1)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true", help="exit 1 when index.html is unpatched")
    args = parser.parse_args(argv)

    path = index_html_path()
    text = path.read_text(encoding="utf-8")
    if MARKER in text:
        print(f"patch_streamlit_splash: already patched ({path})")
        return 0
    if args.check:
        print(f"patch_streamlit_splash: NOT patched ({path})", file=sys.stderr)
        return 1
    patched = patch(text)
    if patched == text:
        print(
            f"patch_streamlit_splash: root div not found in {path}; Streamlit's index.html "
            "changed shape, nothing written",
            file=sys.stderr,
        )
        return 1
    path.write_text(patched, encoding="utf-8")
    print(f"patch_streamlit_splash: splash written ({path})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
