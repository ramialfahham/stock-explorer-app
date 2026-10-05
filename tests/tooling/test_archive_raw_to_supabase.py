"""Offline tests for the raw archive -- a fake Storage client, no network -- plus its place in
the `data-pipeline` job."""

from __future__ import annotations

import pathlib
from types import SimpleNamespace

import pytest
import yaml

import archive_raw_to_supabase as arc

CI_FILE = pathlib.Path(__file__).resolve().parents[2] / ".gitlab-ci.yml"


class _FakeBucketFiles:
    def __init__(self, objects: dict[str, bytes], fail_on: str | None):
        self.objects = objects
        self.fail_on = fail_on

    def list(self, folder):
        prefix = folder + "/"
        return [{"name": o[len(prefix):]} for o in self.objects if o.startswith(prefix)]

    def upload(self, path, data, file_options=None):
        if path == self.fail_on:
            raise RuntimeError("storage unavailable")
        assert file_options["upsert"] == "false"
        assert path not in self.objects, f"overwrote {path}"
        self.objects[path] = data


class _FakeStorage:
    def __init__(self, buckets=(arc.BUCKET,), objects=None, fail_on=None):
        self.buckets = list(buckets)
        self.created = []
        self.files = _FakeBucketFiles(dict(objects or {}), fail_on)

    def list_buckets(self):
        return [SimpleNamespace(id=b) for b in self.buckets]

    def create_bucket(self, bucket_id, options=None):
        self.created.append((bucket_id, options))
        self.buckets.append(bucket_id)

    def from_(self, bucket_id):
        assert bucket_id == arc.BUCKET
        return self.files


def _client(**kw):
    return SimpleNamespace(storage=_FakeStorage(**kw))


def _raw(tmp_path: pathlib.Path) -> pathlib.Path:
    for market in ("us_sp500", "uk_ftse100"):
        (tmp_path / market).mkdir()
        for name in ("yf_constituents", "yf_daily_prices", "yf_fundamentals"):
            (tmp_path / market / f"{name}.parquet").write_bytes(f"{market}/{name}".encode())
    (tmp_path / ".gitkeep").write_text("")
    return tmp_path


def test_uploads_every_market_file_under_the_run_date_and_run_id(tmp_path):
    client = _client()
    assert arc.archive(client, _raw(tmp_path), "2026-10-05", "9001") == (6, 0)
    objects = client.storage.files.objects
    assert sorted(objects) == sorted(
        f"raw/2026-10-05/9001/{m}/{n}.parquet"
        for m in ("us_sp500", "uk_ftse100")
        for n in ("yf_constituents", "yf_daily_prices", "yf_fundamentals")
    )
    assert (objects["raw/2026-10-05/9001/uk_ftse100/yf_fundamentals.parquet"]
            == b"uk_ftse100/yf_fundamentals")


def test_a_rerun_of_the_same_run_keeps_the_earlier_objects(tmp_path):
    earlier = "raw/2026-10-05/9001/us_sp500/yf_fundamentals.parquet"
    client = _client(objects={earlier: b"first run"})
    assert arc.archive(client, _raw(tmp_path), "2026-10-05", "9001") == (5, 1)
    assert client.storage.files.objects[earlier] == b"first run"


def test_another_date_is_a_separate_folder(tmp_path):
    client = _client(objects={"raw/2026-10-04/9001/us_sp500/yf_fundamentals.parquet": b"old"})
    assert arc.archive(client, _raw(tmp_path), "2026-10-05", "9001") == (6, 0)


def test_another_run_on_the_same_day_is_a_separate_folder(tmp_path):
    earlier = "raw/2026-10-05/9000/us_sp500/yf_fundamentals.parquet"
    client = _client(objects={earlier: b"earlier run"})
    assert arc.archive(client, _raw(tmp_path), "2026-10-05", "9001") == (6, 0)
    assert client.storage.files.objects[earlier] == b"earlier run"


def test_creates_the_bucket_private_when_missing(tmp_path):
    client = _client(buckets=())
    arc.archive(client, _raw(tmp_path), "2026-10-05", "9001")
    assert client.storage.created == [(arc.BUCKET, {"public": False})]


def test_an_existing_bucket_is_not_recreated(tmp_path):
    client = _client()
    arc.archive(client, _raw(tmp_path), "2026-10-05", "9001")
    assert client.storage.created == []


def test_main_skips_with_exit_0_when_the_key_is_empty(tmp_path, monkeypatch):
    monkeypatch.setattr(arc, "load_dotenv", lambda: None)
    monkeypatch.setenv("SUPABASE_URL", "https://example.supabase.co")
    monkeypatch.setenv("SUPABASE_SERVICE_ROLE_KEY", "")
    assert arc.main(["--raw-dir", str(_raw(tmp_path))]) == 0


def _main_with(monkeypatch, client, raw_dir, extra=("--run-id", "9001")) -> int:
    import supabase

    monkeypatch.setattr(arc, "load_dotenv", lambda: None)
    monkeypatch.setenv("SUPABASE_URL", "https://example.supabase.co")
    monkeypatch.setenv("SUPABASE_SERVICE_ROLE_KEY", "test-key")
    monkeypatch.setattr(supabase, "create_client", lambda url, key: client)
    return arc.main(["--raw-dir", str(raw_dir), "--run-date", "2026-10-05", *extra])


def test_main_exits_1_when_an_upload_fails(tmp_path, monkeypatch):
    client = _client(fail_on="raw/2026-10-05/9001/uk_ftse100/yf_daily_prices.parquet")
    assert _main_with(monkeypatch, client, _raw(tmp_path)) == 1


def test_main_exits_1_when_there_is_nothing_to_archive(tmp_path, monkeypatch):
    assert _main_with(monkeypatch, _client(), tmp_path) == 1


def test_main_exits_0_after_a_full_upload(tmp_path, monkeypatch):
    client = _client()
    assert _main_with(monkeypatch, client, _raw(tmp_path)) == 0
    assert len(client.storage.files.objects) == 6


@pytest.mark.parametrize("job_id, expected", [("12345", "12345"), (None, "local")])
def test_the_run_id_is_the_ci_job_id_else_local(monkeypatch, job_id, expected):
    if job_id is None:
        monkeypatch.delenv("CI_JOB_ID", raising=False)
    else:
        monkeypatch.setenv("CI_JOB_ID", job_id)
    seen = []

    def fake_archive(client, raw_dir, run_date, run_id):
        seen.append(run_id)
        return 0, 0

    monkeypatch.setattr(arc, "archive", fake_archive)
    assert _main_with(monkeypatch, _client(), pathlib.Path("unused"), extra=[]) == 0
    assert seen == [expected]


def _pipeline_script() -> list[str]:
    return yaml.safe_load(CI_FILE.read_text(encoding="utf-8"))["data-pipeline"]["script"]


def test_the_archive_runs_after_ingestion_and_before_dbt_without_stopping_the_run():
    script = _pipeline_script()
    archive = next(i for i, s in enumerate(script) if "archive_raw_to_supabase.py" in s)
    ingest = next(i for i, s in enumerate(script) if "run_ingestion.py" in s)
    first_dbt = next(i for i, s in enumerate(script) if s.startswith("dbt "))
    assert ingest < archive < first_dbt
    assert "||" in script[archive], "an archive failure must not stop the run"


def test_the_job_fails_at_its_end_when_the_archive_failed():
    script = _pipeline_script()
    archive = next(s for s in script if "archive_raw_to_supabase.py" in s)
    marker = archive.split("touch", 1)[1].strip()
    assert marker in script[-1] and "exit 1" in script[-1]
    assert "generate_assessments.py" in script[-2]
