"""Print pooler host/port from Supabase Management API.

Usage:
    set SUPABASE_ACCESS_TOKEN=sbp_...   # Account → Access Tokens
    set SUPABASE_URL=https://xxx.supabase.co
    python scripts/print_supabase_pooler_config.py
"""

from __future__ import annotations

import os
import sys

from dotenv import load_dotenv

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from scripts.apply_supabase_migrations import (  # noqa: E402
    _fetch_pooler_host_port,
    _project_ref_from_supabase_url,
    _strip_env,
)


def main() -> int:
    load_dotenv()
    url = _strip_env(os.getenv("SUPABASE_URL"))
    token = _strip_env(os.getenv("SUPABASE_ACCESS_TOKEN"))
    if not url or not token:
        print("Set SUPABASE_URL and SUPABASE_ACCESS_TOKEN in .env", file=sys.stderr)
        return 1

    ref = _project_ref_from_supabase_url(url)
    host, port = _fetch_pooler_host_port(ref, token)
    print(f"SUPABASE_DB_HOST={host}")
    print(f"SUPABASE_DB_PORT={port}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
