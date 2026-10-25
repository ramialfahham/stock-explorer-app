"""check_null_when_documented's logic (the raw-passthrough exemption, the not_null-test
lookup, the "mentions null" check) and check_used_by_matches_dependencies against a small fake
manifest -- not a full dbt build."""

from __future__ import annotations

import pytest

from check_dbt_documentation import (  # noqa: E402
    check_null_when_documented,
    check_used_by_matches_dependencies,
)


def _model(name: str, path: str, columns: dict[str, str]) -> tuple[str, dict]:
    unique_id = f"model.dbt_analytics.{name}"
    return unique_id, {
        "resource_type": "model",
        "unique_id": unique_id,
        "name": name,
        "path": path,
        "columns": {col: {"description": desc} for col, desc in columns.items()},
    }


def _not_null_test(model_unique_id: str, column: str) -> tuple[str, dict]:
    return f"test.dbt_analytics.not_null_{model_unique_id}_{column}", {
        "resource_type": "test",
        "test_metadata": {"name": "not_null", "kwargs": {"column_name": column}},
        "depends_on": {"nodes": [model_unique_id]},
    }


def test_flags_a_nullable_computed_column_with_no_null_mention() -> None:
    model_id, model = _model(
        "mart_stock_cards", "5_marts/mart_stock_cards.sql", {"ebit_margin_pct": "Operating margin."}
    )
    manifest = {"nodes": {model_id: model}}
    errors: list[str] = []
    check_null_when_documented(manifest, errors)
    assert len(errors) == 1
    assert "mart_stock_cards.ebit_margin_pct" in errors[0]


def test_accepts_a_description_that_mentions_null() -> None:
    model_id, model = _model(
        "mart_stock_cards",
        "5_marts/mart_stock_cards.sql",
        {"ebit_margin_pct": "Operating margin. Null when inputs are missing."},
    )
    manifest = {"nodes": {model_id: model}}
    errors: list[str] = []
    check_null_when_documented(manifest, errors)
    assert errors == []


def test_case_insensitive_null_mention() -> None:
    model_id, model = _model(
        "mart_stock_cards",
        "5_marts/mart_stock_cards.sql",
        {"ebit_margin_pct": "Operating margin. NULL when inputs are missing."},
    )
    manifest = {"nodes": {model_id: model}}
    errors: list[str] = []
    check_null_when_documented(manifest, errors)
    assert errors == []


def test_exempts_a_column_with_a_not_null_test() -> None:
    model_id, model = _model(
        "mart_stock_cards", "5_marts/mart_stock_cards.sql", {"ticker": "Provider symbol."}
    )
    test_id, test_node = _not_null_test(model_id, "ticker")
    manifest = {"nodes": {model_id: model, test_id: test_node}}
    errors: list[str] = []
    check_null_when_documented(manifest, errors)
    assert errors == []


def test_exempts_a_raw_passthrough_column_by_name_prefix() -> None:
    # info_/stmt_/qtr_ mark a column carried through unmodified from a raw source field
    # (assigned once in staging, e.g. stg_yf__fundamentals.sql, never renamed downstream)
    # -- its nullability is inherited from the provider, not a computed condition to
    # restate in every layer that passes it through.
    model_id, model = _model(
        "fct_fundamentals_snapshot",
        "3_core/fct_fundamentals_snapshot.sql",
        {"info_forward_pe": "Raw Yahoo forwardPE."},
    )
    manifest = {"nodes": {model_id: model}}
    errors: list[str] = []
    check_null_when_documented(manifest, errors)
    assert errors == []


def test_ignores_staging_and_base_layers() -> None:
    # These layers have their own lighter documentation rule (map to source field name,
    # note raw vs derived) -- the full null-when anatomy only applies to core/intermediate/marts.
    model_id, model = _model(
        "stg_yf__fundamentals", "1_staging/yfinance/stg_yf__fundamentals.sql", {"ticker": "Symbol."}
    )
    manifest = {"nodes": {model_id: model}}
    errors: list[str] = []
    check_null_when_documented(manifest, errors)
    assert errors == []


def test_ignores_a_column_with_no_description_at_all() -> None:
    # A missing description is check_column_descriptions' finding, not this check's --
    # avoids reporting the same gap twice under two different messages.
    model_id, model = _model(
        "mart_stock_cards", "5_marts/mart_stock_cards.sql", {"ebit_margin_pct": ""}
    )
    manifest = {"nodes": {model_id: model}}
    errors: list[str] = []
    check_null_when_documented(manifest, errors)
    assert errors == []


def _described_model(
    name: str, description: str, depends_on: list[str], package: str = "dbt_analytics", path: str = ""
) -> tuple[str, dict]:
    unique_id = f"model.{package}.{name}"
    return unique_id, {
        "resource_type": "model",
        "unique_id": unique_id,
        "name": name,
        "package_name": package,
        "path": path,
        "description": description,
        "depends_on": {"nodes": [dep if "." in dep else f"model.dbt_analytics.{dep}" for dep in depends_on]},
    }


def _manifest(*models: tuple[str, dict]) -> dict:
    return {"metadata": {"project_name": "dbt_analytics"}, "nodes": dict(models)}


def _used_by_errors(*models: tuple[str, dict]) -> list[str]:
    errors: list[str] = []
    check_used_by_matches_dependencies(_manifest(*models), errors)
    return errors


def test_used_by_naming_exactly_the_dependents_passes() -> None:
    errors = _used_by_errors(
        _described_model("a", "**Grain:** x. **Used by:** b, c. **Source:** y.", []),
        _described_model("b", "**Grain:** x.", ["a"]),
        _described_model("c", "**Grain:** x.", ["a"]),
    )
    assert errors == []


def test_used_by_naming_a_model_that_does_not_depend_on_it_fails() -> None:
    errors = _used_by_errors(
        _described_model("a", "**Used by:** b, c.", []),
        _described_model("b", "**Grain:** x.", ["a"]),
        _described_model("c", "**Grain:** x.", []),
    )
    assert errors == ["model a: Used by names ['c'] which do not depend on it and leaves out [] which do"]


def test_used_by_leaving_out_a_dependent_model_fails() -> None:
    errors = _used_by_errors(
        _described_model("a", "**Used by:** b.", []),
        _described_model("b", "**Grain:** x.", ["a"]),
        _described_model("c", "**Grain:** x.", ["a"]),
    )
    assert errors == ["model a: Used by names [] which do not depend on it and leaves out ['c'] which do"]


def test_used_by_naming_only_non_model_consumers_passes_when_nothing_depends_on_the_model() -> None:
    errors = _used_by_errors(_described_model("a", "**Used by:** export_to_supabase.py, Streamlit app.", []))
    assert errors == []


def test_used_by_naming_no_model_fails_when_a_model_depends_on_it() -> None:
    errors = _used_by_errors(
        _described_model("a", "**Used by:** the Streamlit app.", []),
        _described_model("b", "**Grain:** x.", ["a"]),
    )
    assert len(errors) == 1


@pytest.mark.parametrize("path", ["1_staging/a.sql", "2_base/a.sql", ""])
def test_a_staging_or_base_model_without_a_used_by_line_is_skipped(path: str) -> None:
    errors = _used_by_errors(
        _described_model("a", "**Grain:** x. **Source:** y.", [], path=path),
        _described_model("b", "**Grain:** x.", ["a"]),
    )
    assert errors == []


@pytest.mark.parametrize("path", ["3_core/a.sql", "4_intermediate/a.sql", "5_marts/a.sql", "5_marts\\a.sql"])
def test_a_core_intermediate_or_mart_model_without_a_used_by_line_fails(path: str) -> None:
    errors = _used_by_errors(_described_model("a", "**Grain:** x. **Source:** y.", [], path=path))
    assert errors == ["model a: description has no **Used by:** line"]


def test_a_mart_model_with_a_used_by_line_passes() -> None:
    errors = _used_by_errors(_described_model("a", "**Used by:** the Streamlit app.", [], path="5_marts/a.sql"))
    assert errors == []


def test_a_model_name_that_contains_another_is_not_a_match_for_it() -> None:
    errors = _used_by_errors(
        _described_model("fct", "**Used by:** fct_extra.", []),
        _described_model("fct_extra", "**Grain:** x.", ["fct"]),
    )
    assert errors == []


def test_models_of_another_package_are_ignored() -> None:
    errors = _used_by_errors(
        _described_model("a", "**Used by:** b.", []),
        _described_model("b", "**Grain:** x.", ["a"]),
        _described_model("c", "**Grain:** x.", ["model.dbt_analytics.a"], package="dbt_utils"),
    )
    assert errors == []


def test_main_runs_the_used_by_check(monkeypatch, capsys) -> None:
    import check_dbt_documentation as module

    monkeypatch.setattr(module, "_load_json", lambda path: {})
    for other in ("check_model_descriptions", "check_column_descriptions", "check_null_when_documented"):
        monkeypatch.setattr(module, other, lambda *args, **kwargs: None)
    monkeypatch.setattr(module, "check_sources", lambda errors: None)
    monkeypatch.setattr(
        module, "check_used_by_matches_dependencies", lambda manifest, errors: errors.append("model x: Used by is wrong")
    )

    assert module.main() == 1
    assert "model x: Used by is wrong" in capsys.readouterr().out
