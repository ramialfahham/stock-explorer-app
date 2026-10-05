"""Archive this run's raw ingestion parquet to private Supabase Storage (service role).

Uploads every `storage/raw/<market>/*.parquet` to bucket `raw-archive` at
`raw/<run date, UTC>/<run id>/<market>/<file>`. The run id is the GitLab job id
(CI_JOB_ID), new on every attempt including a retry, so no two runs share a folder; it is
`local` outside CI. Append-only: an object already archived under that folder is kept and
skipped, never overwritten. The bucket is created, private, when missing.

Exit codes: 0 when everything was archived or skipped, and also when SUPABASE_URL or
SUPABASE_SERVICE_ROLE_KEY is unset (nothing to archive to). 1 on any failure, including an
empty raw folder. `data-pipeline` in .gitlab-ci.yml keeps running after a 1 and fails the job
at its end, so the cards still refresh and the gap is still visible.
"""

from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RAW_DIR = REPO_ROOT / "storage" / "raw"
BUCKET = "raw-archive"


def planned_objects(raw_dir: Path, run_date: str, run_id: str) -> list[tuple[Path, str]]:
    """(local file, object path) for every market's raw parquet, sorted by object path."""
    return sorted(
        ((p, f"raw/{run_date}/{run_id}/{p.parent.name}/{p.name}")
         for p in raw_dir.glob("*/*.parquet")),
        key=lambda pair: pair[1],
    )


def _ensure_bucket(client) -> None:
    if not any(b.id == BUCKET for b in client.storage.list_buckets()):
        client.storage.create_bucket(BUCKET, options={"public": False})


def archive(client, raw_dir: Path, run_date: str, run_id: str) -> tuple[int, int]:
    """Upload what is not yet archived for this run. Returns (uploaded, skipped)."""
    objects = planned_objects(raw_dir, run_date, run_id)
    if not objects:
        raise RuntimeError(f"no raw parquet under {raw_dir}")
    _ensure_bucket(client)
    store = client.storage.from_(BUCKET)
    existing: dict[str, set[str]] = {}
    uploaded = skipped = 0
    for local, obj in objects:
        folder, name = obj.rsplit("/", 1)
        if folder not in existing:
            existing[folder] = {entry["name"] for entry in store.list(folder)}
        if name in existing[folder]:
            print(f"  skip (already archived): {obj}")
            skipped += 1
            continue
        store.upload(obj, local.read_bytes(),
                     file_options={"content-type": "application/octet-stream", "upsert": "false"})
        uploaded += 1
    return uploaded, skipped


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--raw-dir", type=Path, default=DEFAULT_RAW_DIR)
    parser.add_argument("--run-date", default=datetime.now(timezone.utc).date().isoformat(),
                        help="archive folder date, YYYY-MM-DD (default: today, UTC)")
    parser.add_argument("--run-id", default=os.getenv("CI_JOB_ID") or "local",
                        help="archive folder under the date (default: CI_JOB_ID, else local)")
    args = parser.parse_args(argv)

    load_dotenv()
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not key:
        print("Raw archive skipped: SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY not set.")
        return 0

    try:
        from supabase import create_client

        uploaded, skipped = archive(create_client(url, key), args.raw_dir, args.run_date,
                                    args.run_id)
    except Exception as exc:
        print(f"Raw archive FAILED: {exc}", file=sys.stderr)
        return 1
    print(f"Raw archive {args.run_date}/{args.run_id}: {uploaded} uploaded, "
          f"{skipped} already archived.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
