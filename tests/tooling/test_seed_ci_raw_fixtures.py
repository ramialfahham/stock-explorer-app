"""seed_ci_raw_fixtures.py --out-dir: the proof command seeds fixtures into a throwaway folder,
so it must never write the default storage/raw, where real ingested data lives."""

from __future__ import annotations

from pathlib import Path

import pytest

import seed_ci_raw_fixtures as seed


def test_out_dir_receives_every_market_and_the_default_is_untouched(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    default = tmp_path / "default_raw"
    out = tmp_path / "verify_raw"
    monkeypatch.setattr(seed, "DEFAULT_RAW_DIR", default)

    assert seed.main(["--out-dir", str(out)]) == 0

    markets = seed._load_active_markets()
    assert markets
    for market in markets:
        for name in ("yf_constituents", "yf_daily_prices", "yf_fundamentals"):
            assert (out / market / f"{name}.parquet").is_file()
    assert not default.exists()
