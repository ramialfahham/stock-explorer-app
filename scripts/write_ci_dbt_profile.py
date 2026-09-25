#!/usr/bin/env python3
"""Write dbt's CI DuckDB profile to `$HOME/.dbt/profiles.yml`, or into `--profiles-dir`.

Replaces three near-identical heredocs in `.gitlab-ci.yml` (`validate:full`, `data-pipeline`,
`dev-schema-check`) that differed only in the `path:` value -- not parameterizable via a plain
YAML anchor, so the profile-writing moved into a script instead, matching this repo's existing
pattern of pulling repeated CI logic into `scripts/*.py`.

Usage:
    python scripts/write_ci_dbt_profile.py --path /tmp/stock_data_ci.db
"""

from __future__ import annotations

import argparse
from pathlib import Path

PROFILE_TEMPLATE = """dbt_analytics:
  target: ci
  outputs:
    ci:
      type: duckdb
      path: {path}
      threads: 4
"""


def write_profile(path: str, home: Path | None = None, profiles_dir: Path | None = None) -> Path:
    dbt_dir = profiles_dir or (home or Path.home()) / ".dbt"
    dbt_dir.mkdir(parents=True, exist_ok=True)
    profile_path = dbt_dir / "profiles.yml"
    profile_path.write_text(PROFILE_TEMPLATE.format(path=path), encoding="utf-8")
    return profile_path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--path", required=True, help="DuckDB file path for the ci target")
    parser.add_argument(
        "--profiles-dir", type=Path, help="folder for profiles.yml (default: $HOME/.dbt)"
    )
    args = parser.parse_args()
    profile_path = write_profile(args.path, profiles_dir=args.profiles_dir)
    print(f"Wrote {profile_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
