"""Tests for the manual constituent import."""

from __future__ import annotations

import pandas as pd

import import_constituents
from ingestion.constituents import seeds


def test_import_keeps_the_ticker_na(tmp_path, monkeypatch) -> None:
    source = tmp_path / "import.csv"
    source.write_text(
        "ticker,company_name\nAEM,Agnico Eagle\nNA,National Bank of Canada\n", encoding="utf-8"
    )
    out = tmp_path / "constituents.csv"
    monkeypatch.setattr(seeds, "seed_path", lambda code: out)

    assert import_constituents.main(["--market", "ca_tsx60", "--file", str(source)]) == 0

    written = pd.read_csv(out, dtype=str, na_filter=False)
    assert written["ticker"].tolist() == ["AEM", "NA"]


def test_import_fails_on_a_row_without_a_name(tmp_path, monkeypatch) -> None:
    source = tmp_path / "import.csv"
    source.write_text("ticker,company_name\nAEM,Agnico Eagle\nNA,\n", encoding="utf-8")
    out = tmp_path / "constituents.csv"
    monkeypatch.setattr(seeds, "seed_path", lambda code: out)

    assert import_constituents.main(["--market", "ca_tsx60", "--file", str(source)]) == 1
    assert not out.exists()
