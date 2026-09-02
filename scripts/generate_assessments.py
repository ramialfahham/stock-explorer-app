"""Generate per-card health assessments from the DuckDB mart into Supabase (Slice 5).

Two layers:
- 5a (deterministic, no LLM): reads marts.mart_stock_cards (already filtered to eligible
  cards), computes a per-type health verdict + an input_hash per card.
- 5b (Claude Haiku prose read): fills ai_read / read_model, calling Claude ONLY when a
  card's input_hash changed or its stored ai_read is null (regenerate-on-change). The read
  is educational, never advice, and reasons only from the card's own numbers.

Mirrors scripts/export_to_supabase.py for the read/coerce/upsert shape. --dry-run returns
before any credential or LLM call, so CI can smoke it secret-free; the real path also skips
the reads when ANTHROPIC_API_KEY is absent. A base record omits ai_read / read_model unless
a fresh read was generated, so a re-run never clobbers a stored read (PostgREST upsert only
sets the columns provided).
"""

from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import anthropic
import duckdb
import pandas as pd
from dotenv import load_dotenv
from supabase import create_client

from assessment_rules import (
    INPUT_FIELDS_BY_TYPE,
    READ_TOOL_NAME,
    READ_TOOL_SCHEMA,
    build_read_messages,
    compute_input_hash,
    compute_verdict,
    validate_read_metrics,
)

REPO_ROOT = Path(__file__).resolve().parents[1]

# Slice 5b: the Claude Haiku prose read. READ_MODEL is the request model; the id
# actually stored in read_model is response.model (echoed back by the API).
READ_MODEL = "claude-haiku-4-5"
# Forced tool-use (READ_TOOL_SCHEMA) adds JSON structure on top of the prose itself -- the
# read's own 2-3 sentences plus a handful of {label, value_as_shown} pairs -- so this is higher
# than a free-text call would need, to avoid truncating the read to make room for the wrapper.
READ_MAX_TOKENS = 512

# Union of every per-type card metric (derived from the rules module so it can't drift),
# plus the keys the verdict/hash and dedupe need. `currency` is named to the model whenever
# it is present, on every card type, and is part of the input hash, so a corrected currency
# regenerates the read.
_METRIC_COLUMNS = sorted({m for fields in INPUT_FIELDS_BY_TYPE.values() for m in fields})
ASSESSMENT_INPUT_COLUMNS = [
    "market_code",
    "ticker",
    "company_type",
    "currency",
    "snapshot_date",
    # Verdict-computation signals, not displayed metrics -- deliberately NOT routed through
    # INPUT_FIELDS_BY_TYPE (that set is specifically "the full displayed set per type" per its
    # own docstring). Feed _verdict_operating's two sign-inversion guards: info_ebitda tells
    # genuine net cash apart from a ratio flipped by negative EBITDA; stmt_stockholders_equity
    # tells genuine low leverage apart from a ratio flipped by negative equity, checked directly
    # rather than inferred from debt_to_equity's own sign (unreliable when total debt is exactly
    # zero). Neither is hashed separately since compute_input_hash already hashes the computed
    # verdict itself, and a verdict either guard changes already moves it.
    "info_ebitda",
    "stmt_stockholders_equity",
    # Feeds current_ratio_stmt's joint-liquidity-evaluation relief: a real dollar comparison of
    # free cash flow against the working-capital shortfall, rather than fcf_margin_pct's
    # revenue-scaled proxy. working_capital itself is NOT added here -- it's already part of
    # _METRIC_COLUMNS below via INPUT_FIELDS_BY_TYPE["pre_revenue"], so every row already carries
    # it regardless of company_type (the mart computes it unconditionally).
    "stmt_free_cash_flow",
    *_METRIC_COLUMNS,
]


def _coerce(value):
    """Match export_to_supabase coercion: NaN/NA -> None, dates -> iso, numpy -> python."""
    if value is None or pd.isna(value):
        return None
    if isinstance(value, float) and value != value:  # defensive NaN
        return None
    if hasattr(value, "isoformat"):
        return value.isoformat()
    if hasattr(value, "item"):
        return value.item()
    return value


def _load_mart_rows(db_path: Path) -> list[dict]:
    conn = duckdb.connect(str(db_path), read_only=True)
    try:
        cols = ", ".join(ASSESSMENT_INPUT_COLUMNS)
        frame = conn.execute(f"select {cols} from marts.mart_stock_cards").fetchdf()
    finally:
        conn.close()
    if frame.empty:
        return []
    return [
        {col: _coerce(row[col]) for col in ASSESSMENT_INPUT_COLUMNS}
        for _, row in frame.iterrows()
    ]


def _latest_per_ticker(rows: list[dict]) -> list[dict]:
    """Keep the row with the max snapshot_date per (market_code, ticker)."""
    latest: dict[tuple, dict] = {}
    for row in rows:
        key = (row["market_code"], row["ticker"])
        current = latest.get(key)
        if current is None or str(row["snapshot_date"]) > str(current["snapshot_date"]):
            latest[key] = row
    return list(latest.values())


def build_assessment_records(rows: list[dict]) -> list[dict]:
    """Pure: dedupe to latest snapshot, then verdict + input_hash per card.

    ai_read / read_model are intentionally omitted (not None) so a 5a upsert never nulls a
    Slice-5b prose read.
    """
    generated_at = datetime.now(timezone.utc).isoformat()
    records: list[dict] = []
    for row in _latest_per_ticker(rows):
        verdict = compute_verdict(row)
        records.append(
            {
                "market_code": row["market_code"],
                "ticker": row["ticker"],
                "company_type": row["company_type"],
                "health_verdict": verdict,
                "input_hash": compute_input_hash(row, verdict),
                "snapshot_date": row["snapshot_date"],
                "generated_at": generated_at,
            }
        )
    return records


def _verdict_distribution(records: list[dict]) -> dict[str, int]:
    dist: dict[str, int] = {}
    for rec in records:
        dist[rec["health_verdict"]] = dist.get(rec["health_verdict"], 0) + 1
    return dist


# --- Slice 5b: the Claude Haiku prose read (regenerate-on-change) -------------


def _fetch_existing_assessments(client) -> dict[tuple, dict]:
    """Read the stored (input_hash, ai_read, read_model) per card so we can skip
    unchanged ones. At current scale (tens of eligible cards) a single select is well
    under PostgREST's default row cap."""
    resp = (
        client.table("card_assessments")
        .select("market_code,ticker,input_hash,ai_read,read_model")
        .execute()
    )
    rows = resp.data or []
    return {(r["market_code"], r["ticker"]): r for r in rows}


def _generate_read(client, row: dict, verdict: str) -> tuple[str | None, str | None]:
    """Call Claude Haiku for one card's prose read. Returns (text, model_id), or
    (None, None) on any failure so a single bad card never fails the batch.

    Forces tool-use (READ_TOOL_SCHEMA) so the model returns the read alongside the exact
    metrics it cited, then checks those against the card's own numbers (validate_read_metrics)
    before accepting the read -- a malformed response, an empty read, or any citation that
    doesn't match the data is treated the same as an API failure: fail closed, self-heals next
    run via the existing regenerate-on-input-hash-change path. No retry.
    """
    system, user = build_read_messages(row, verdict)
    try:
        resp = client.messages.create(
            model=READ_MODEL,
            max_tokens=READ_MAX_TOKENS,
            system=system,
            messages=[{"role": "user", "content": user}],
            tools=[READ_TOOL_SCHEMA],
            tool_choice={"type": "tool", "name": READ_TOOL_NAME},
        )
    except Exception as exc:  # noqa: BLE001 - resilience: isolate one card's failure
        print(
            f"  read failed for {row.get('market_code')}/{row.get('ticker')}: {exc}",
            file=sys.stderr,
        )
        return None, None
    tool_block = next(
        (block for block in resp.content if getattr(block, "type", None) == "tool_use"),
        None,
    )
    if tool_block is None:
        print(
            f"  read failed for {row.get('market_code')}/{row.get('ticker')}: "
            f"no tool_use block in response (stop_reason={getattr(resp, 'stop_reason', None)!r})",
            file=sys.stderr,
        )
        return None, None
    payload = tool_block.input if isinstance(tool_block.input, dict) else {}
    text = str(payload.get("read") or "").strip()
    referenced = payload.get("referenced_metrics")
    if not text or not isinstance(referenced, list):
        print(
            f"  read failed for {row.get('market_code')}/{row.get('ticker')}: "
            f"malformed tool payload (read={'present' if text else 'blank'}, "
            f"referenced_metrics type={type(referenced).__name__})",
            file=sys.stderr,
        )
        return None, None
    if not validate_read_metrics(row, referenced):
        print(
            f"  read REJECTED (unverifiable metric) for "
            f"{row.get('market_code')}/{row.get('ticker')}",
            file=sys.stderr,
        )
        return None, None
    return text, resp.model


def attach_reads(
    records: list[dict],
    rows_by_key: dict[tuple, dict],
    existing_by_key: dict[tuple, dict],
    client,
) -> dict[str, int]:
    """Fill ai_read / read_model on records that changed, in place.

    Regenerate a card's read when it is new, its input_hash differs from the stored
    one, or its stored ai_read is empty. Otherwise leave both keys ABSENT so the upsert
    preserves the stored read (never clobbers). A per-card API failure also leaves the
    keys absent, so the card stays null-read and retries next run (self-healing).
    """
    generated = carried = failed = 0
    for record in records:
        key = (record["market_code"], record["ticker"])
        existing = existing_by_key.get(key)
        if existing is None:
            regenerate = True
        else:
            regenerate = (
                existing.get("input_hash") != record["input_hash"]
                or not existing.get("ai_read")
            )
        if not regenerate:
            carried += 1
            continue
        row = rows_by_key.get(key)
        if row is None:  # defensive: records derive from these rows, so shouldn't happen
            failed += 1
            continue
        text, model = _generate_read(client, row, record["health_verdict"])
        if text is None:
            failed += 1
            continue
        record["ai_read"] = text
        record["read_model"] = model
        generated += 1
    return {"generated": generated, "carried": carried, "failed": failed}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Generate card_assessments verdicts + Claude Haiku reads from the DuckDB mart (Slice 5)"
    )
    parser.add_argument(
        "--duckdb-path",
        default=str(REPO_ROOT / "storage" / "stock_data.db"),
        help="Path to DuckDB file after dbt build",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Compute verdicts but do not write to Supabase (no credentials required)",
    )
    args = parser.parse_args(argv)

    load_dotenv()

    db_path = Path(args.duckdb_path)
    if not db_path.exists():
        print(f"DuckDB not found: {db_path}", file=sys.stderr)
        return 1

    rows = _load_mart_rows(db_path)
    records = build_assessment_records(rows)
    print(
        f"generate_assessments: {len(records)} cards -> verdicts {_verdict_distribution(records)}"
    )

    # Dry-run returns before touching credentials so CI can smoke it secret-free.
    if args.dry_run:
        return 0

    if not records:
        print("Nothing to generate; keeping existing card_assessments snapshot.")
        return 0

    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not key:
        print("Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY in .env", file=sys.stderr)
        return 1

    client = create_client(url, key)

    # Slice 5b: fill ai_read / read_model for changed cards only. Skipped when no
    # ANTHROPIC_API_KEY (verdicts still upsert, as in 5a) so the pipeline degrades
    # gracefully and the secret is a soft dependency.
    if os.getenv("ANTHROPIC_API_KEY"):
        existing = _fetch_existing_assessments(client)
        rows_by_key = {
            (r["market_code"], r["ticker"]): r for r in _latest_per_ticker(rows)
        }
        summary = attach_reads(records, rows_by_key, existing, anthropic.Anthropic())
        print(
            "generate_assessments: reads "
            f"generated={summary['generated']} carried={summary['carried']} "
            f"failed={summary['failed']}"
        )
    else:
        print(
            "generate_assessments: no ANTHROPIC_API_KEY, skipping prose reads (verdicts only)"
        )

    batch_size = 500
    for start in range(0, len(records), batch_size):
        batch = records[start : start + batch_size]
        client.table("card_assessments").upsert(
            batch, on_conflict="market_code,ticker"
        ).execute()

    print(f"generate_assessments: upserted {len(records)} rows")
    return 0


if __name__ == "__main__":
    sys.exit(main())
