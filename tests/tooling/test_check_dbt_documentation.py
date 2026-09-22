"""check_null_when_documented's logic (the raw-passthrough exemption, the not_null-test
lookup, the "mentions null" check) against a small fake manifest -- not a full dbt build."""

from __future__ import annotations

from check_dbt_documentation import check_null_when_documented  # noqa: E402


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
