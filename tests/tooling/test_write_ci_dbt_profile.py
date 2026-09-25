"""write_ci_dbt_profile.py has one job: write a DuckDB dbt profile at $HOME/.dbt/profiles.yml
with a caller-given path. Each test proves the written file is exactly what dbt needs, not
just that a file appears."""

from __future__ import annotations

from pathlib import Path

import yaml

from write_ci_dbt_profile import write_profile  # noqa: E402


def test_writes_profiles_yaml_with_the_given_path(tmp_path: Path) -> None:
    profile_path = write_profile("/tmp/stock_data_ci.db", home=tmp_path)

    assert profile_path == tmp_path / ".dbt" / "profiles.yml"
    parsed = yaml.safe_load(profile_path.read_text(encoding="utf-8"))
    assert parsed == {
        "dbt_analytics": {
            "target": "ci",
            "outputs": {
                "ci": {
                    "type": "duckdb",
                    "path": "/tmp/stock_data_ci.db",
                    "threads": 4,
                }
            },
        }
    }


def test_different_paths_produce_different_profiles(tmp_path: Path) -> None:
    profile_path = write_profile("storage/stock_data.db", home=tmp_path)

    parsed = yaml.safe_load(profile_path.read_text(encoding="utf-8"))
    assert parsed["dbt_analytics"]["outputs"]["ci"]["path"] == "storage/stock_data.db"


def test_creates_the_dbt_directory_if_missing(tmp_path: Path) -> None:
    home = tmp_path / "does" / "not" / "exist" / "yet"

    profile_path = write_profile("/tmp/x.db", home=home)

    assert profile_path.is_file()
    assert profile_path.parent == home / ".dbt"


def test_profiles_dir_writes_there_and_not_under_home(tmp_path: Path) -> None:
    home = tmp_path / "home"
    target = tmp_path / "verify"

    profile_path = write_profile("x.db", home=home, profiles_dir=target)

    assert profile_path == target / "profiles.yml"
    assert not (home / ".dbt").exists()


def test_rerunning_overwrites_rather_than_appends(tmp_path: Path) -> None:
    write_profile("/tmp/first.db", home=tmp_path)
    profile_path = write_profile("/tmp/second.db", home=tmp_path)

    parsed = yaml.safe_load(profile_path.read_text(encoding="utf-8"))
    assert parsed["dbt_analytics"]["outputs"]["ci"]["path"] == "/tmp/second.db"
    assert profile_path.read_text(encoding="utf-8").count("dbt_analytics:") == 1
