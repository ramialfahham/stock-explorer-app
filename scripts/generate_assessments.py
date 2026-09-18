"""Generate per-card health assessments from the DuckDB mart into Supabase (Slice 5).

Two layers:
- 5a (deterministic, no LLM): reads marts.mart_stock_cards (already filtered to eligible
  cards), computes a per-type health verdict + an input_hash per card.
- 5b (Claude Haiku prose read): fills ai_read / read_model, calling Claude ONLY when a
  card's input_hash changed or its stored ai_read is null (regenerate-on-change). The read
  is educational, never advice, and reasons only from the card's own numbers. --max-reads
  caps how many NEW calls a single run makes (unbounded by default); cards with no stored
  read are filled first, anything the cap does not reach becomes eligible again next run. A
  card the cap skips, or whose call fails, has any stale stored read explicitly cleared
  rather than left showing under this run's fresh verdict and numbers.

Mirrors scripts/export_to_supabase.py for the read/coerce/upsert shape and for --target
(prod writes public.card_assessments, dev writes dev.card_assessments in the same project;
dev needs the schema exposed to PostgREST, see docs/supabase_setup.md). --dry-run returns
before any credential or LLM call, so CI can smoke it secret-free; the real path also skips
the reads when ANTHROPIC_API_KEY is absent or empty. A base record omits ai_read / read_model unless
a fresh read was generated, so a re-run never clobbers a stored read -- true only because
_upsert_records() groups each upsert call by a record's exact set of present keys; a plain
single upsert call mixing "has a read" and "omits it" records does NOT preserve the omitted
one (see _upsert_records()'s own docstring -- a real production incident, not a hypothetical).
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
from supabase.lib.client_options import SyncClientOptions

from assessment_rules import (
    INPUT_FIELDS_BY_TYPE,
    READ_TOOL_NAME,
    READ_TOOL_SCHEMA,
    build_read_messages,
    compute_input_hash,
    compute_verdict,
    find_read_style_violations,
    validate_read_metrics,
    verdict_meaning_violation,
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
    # Names operating margin the way the card face does on this row ("(TTM)" or "(annual)");
    # see assessment_rules.read_metric_label. Not a number, so not hashed.
    "ebit_margin_basis",
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


# PostgREST's default per-request row cap. An unranged select silently truncates past this
# many rows -- every card past the cutoff would look permanently new to attach_reads() on
# every run, since it would never appear in existing_by_key at all.
_SELECT_PAGE_SIZE = 1000


def _fetch_existing_assessments(client) -> dict[tuple, dict]:
    """Read the stored (input_hash, ai_read, read_model) per card so we can skip
    unchanged ones. Paginated past PostgREST's default row cap (_SELECT_PAGE_SIZE)."""
    rows: list[dict] = []
    start = 0
    while True:
        resp = (
            client.table("card_assessments")
            .select("market_code,ticker,input_hash,ai_read,read_model")
            .range(start, start + _SELECT_PAGE_SIZE - 1)
            .execute()
        )
        page = resp.data or []
        rows.extend(page)
        if len(page) < _SELECT_PAGE_SIZE:
            break
        start += _SELECT_PAGE_SIZE
    return {(r["market_code"], r["ticker"]): r for r in rows}


def _generate_read(client, row: dict, verdict: str) -> tuple[str | None, str | None]:
    """Call Claude Haiku for one card's prose read. Returns (text, model_id), or
    (None, None) on any failure so a single bad card never fails the batch.

    Forces tool-use (READ_TOOL_SCHEMA) so the model returns the read alongside the exact
    metrics it cited and its own verdict_meaning classification, then checks those against the
    card's own numbers (validate_read_metrics), the verdict already decided (verdict_meaning_violation),
    and a deterministic subset of the prompt's own style rules (find_read_style_violations)
    before accepting the read -- a malformed response, an empty read, an unverifiable citation,
    a verdict-meaning mismatch, or a style-rule violation is treated the same as an API failure:
    fail closed, self-heals next run via the existing regenerate-on-input-hash-change path. No
    retry.
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
    reported_meaning = payload.get("verdict_meaning")
    if not text or not isinstance(referenced, list) or not isinstance(reported_meaning, str):
        print(
            f"  read failed for {row.get('market_code')}/{row.get('ticker')}: "
            f"malformed tool payload (read={'present' if text else 'blank'}, "
            f"referenced_metrics type={type(referenced).__name__}, "
            f"verdict_meaning type={type(reported_meaning).__name__})",
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
    meaning_violation = verdict_meaning_violation(verdict, text, reported_meaning)
    if meaning_violation:
        print(
            f"  read REJECTED (verdict meaning: {meaning_violation}) for "
            f"{row.get('market_code')}/{row.get('ticker')}",
            file=sys.stderr,
        )
        return None, None
    style_violations = find_read_style_violations(text)
    if style_violations:
        print(
            f"  read REJECTED (style: {'; '.join(style_violations)}) for "
            f"{row.get('market_code')}/{row.get('ticker')}",
            file=sys.stderr,
        )
        return None, None
    return text, resp.model


def _clear_stale_read_if_present(record: dict, existing_by_key: dict[tuple, dict]) -> None:
    """A stored read from a PRIOR input_hash must never render next to this run's fresh
    verdict and metrics as if it were current. build_assessment_records() (5a) always writes
    a fresh verdict/snapshot_date/input_hash for every eligible card regardless of whether
    5b's read succeeds -- and the frontend's only staleness guard, attach_assessments()'s
    snapshot_date comparison (frontend/explore_filters.py), does not see input_hash at all,
    so it cannot catch this (equity-analyst-reviewer finding). Leaving the keys merely ABSENT
    -- fine when there was nothing stored -- would let that old prose sit under this run's
    new numbers, silently contradicting them, exactly the "verdict printed over the wrong
    snapshot" failure attach_assessments()'s own docstring calls worse than no verdict at
    all, just on the read instead of the badge.

    Explicit `None` (not an absent key) tells the upsert to actually null the stored columns,
    so the card falls back to VERDICT_FALLBACK_READ -- the same honest, already-designed-for
    "not yet written" state a brand-new card gets, never a placeholder. A no-op when nothing
    was stored (an absent existing.ai_read means there is nothing stale to clear).

    Covers both callers below: a record left behind by --max-reads' cap, and one whose
    generation attempt failed outright -- the same stale-masking risk either way, not a
    cap-specific one.
    """
    key = (record["market_code"], record["ticker"])
    existing = existing_by_key.get(key)
    if existing is not None and existing.get("ai_read"):
        record["ai_read"] = None
        record["read_model"] = None


def attach_reads(
    records: list[dict],
    rows_by_key: dict[tuple, dict],
    existing_by_key: dict[tuple, dict],
    client,
    *,
    max_reads: int | None = None,
) -> dict[str, int]:
    """Fill ai_read / read_model on records that changed, in place.

    Regenerate a card's read when it is new, its input_hash differs from the stored
    one, or its stored ai_read is empty. Otherwise leave both keys ABSENT so the upsert
    preserves the stored read (never clobbers). A per-card API failure, or a card the
    --max-reads cap does not reach this run, clears any stale stored read instead
    (_clear_stale_read_if_present) rather than leaving old prose under new numbers.

    `max_reads` bounds how many NEW Claude calls this run makes -- the AI-read step is the
    scheduled pipeline's dominant, previously-ungoverned runtime cost (~39 of ~65 minutes on
    a 9-market run), the likely long-term driver toward the CI job's 2h timeout as more
    markets are onboarded. `None` (the default) is unbounded -- unchanged behavior; the
    actual production value is an owner call, set via --max-reads. A negative value is
    clamped to 0 (fully capped -- the safe direction for a cost guard) rather than trusted:
    Python slicing treats a negative stop index as "count back from the end", so an unguarded
    `list[:-1]` on a typo would keep nearly everything, the opposite of what the flag exists
    to prevent.

    Cards with NO stored read (new, or a stored ai_read that is empty) are prioritized over
    cards that only need a refresh (input_hash changed but a read already exists) -- a bare
    verdict badge with the deterministic fallback text is a worse gap than a slightly stale
    read, and every card in the fallback state already renders a plain, honest one-liner
    (VERDICT_FALLBACK_READ in card_copy.py), never a placeholder. Both buckets keep the
    records' own relative order, so which cards get capped under a tight budget is
    deterministic, not run-to-run noise -- though a market whose rows sort later in the
    DuckDB scan (no ORDER BY today) can end up consistently behind a market with heavier
    new-card churn; not addressed here, a fair-share rotation across markets would be its own
    design.
    """
    no_stored_read: list[dict] = []  # new card, or a stored ai_read that is empty
    needs_refresh: list[dict] = []  # a read exists, but input_hash changed
    carried = 0
    for record in records:
        key = (record["market_code"], record["ticker"])
        existing = existing_by_key.get(key)
        if existing is None or not existing.get("ai_read"):
            no_stored_read.append(record)
        elif existing.get("input_hash") != record["input_hash"]:
            needs_refresh.append(record)
        else:
            carried += 1
            print(f"  read carried for {record['market_code']}/{record['ticker']} (unchanged)")

    new_first = no_stored_read + needs_refresh
    if max_reads is None:
        selected, capped_records = new_first, []
    else:
        cutoff = max(max_reads, 0)
        selected, capped_records = new_first[:cutoff], new_first[cutoff:]
    for record in capped_records:
        print(f"  read capped for {record['market_code']}/{record['ticker']} (not attempted this run)")
        _clear_stale_read_if_present(record, existing_by_key)

    generated = failed = 0
    for record in selected:
        key = (record["market_code"], record["ticker"])
        row = rows_by_key.get(key)
        if row is None:  # defensive: records derive from these rows, so shouldn't happen
            print(
                f"  read failed for {record['market_code']}/{record['ticker']}: "
                "no matching mart row (defensive branch hit)",
                file=sys.stderr,
            )
            failed += 1
            _clear_stale_read_if_present(record, existing_by_key)
            continue
        text, model = _generate_read(client, row, record["health_verdict"])
        if text is None:
            failed += 1
            _clear_stale_read_if_present(record, existing_by_key)
            continue
        record["ai_read"] = text
        record["read_model"] = model
        generated += 1
        print(f"  read generated for {record['market_code']}/{record['ticker']}")
    return {
        "generated": generated,
        "carried": carried,
        "capped": len(capped_records),
        "failed": failed,
    }


def _upsert_records(client, records: list[dict], *, batch_size: int = 500) -> int:
    """Upsert records in batches grouped by their exact set of present keys.

    A single upsert call's `columns` query parameter is the UNION of keys across every
    record it carries (postgrest-py's `_unique_columns`, called from `pre_upsert`; the
    client's own `default_to_null=True` default never sends `Prefer: missing=default`). A
    record that omits a column present on another record in the SAME call has that column
    explicitly nulled by PostgREST, not left untouched -- so a "carried" record (omits
    `ai_read`/`read_model` to keep the stored value) sharing a call with a "generated" one
    gets that value nulled too.

    Grouping every upsert call by `frozenset(record.keys())` before chunking guarantees each
    call is internally homogeneous, so its `columns` union always matches exactly what every
    record in that call provides -- no cross-record contamination, independent of exactly
    how PostgREST or postgrest-py resolve a missing column on merge. Returns the number of
    upsert calls made (test/diagnostic use).
    """
    groups: dict[frozenset, list[dict]] = {}
    for record in records:
        groups.setdefault(frozenset(record.keys()), []).append(record)
    calls = 0
    for group_records in groups.values():
        for start in range(0, len(group_records), batch_size):
            batch = group_records[start : start + batch_size]
            client.table("card_assessments").upsert(
                batch, on_conflict="market_code,ticker"
            ).execute()
            calls += 1
    return calls


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
    parser.add_argument(
        "--target",
        choices=["prod", "dev"],
        default="prod",
        help="prod (default) writes to public.*; dev writes to dev.* in the same project",
    )
    parser.add_argument(
        "--max-reads",
        type=int,
        default=None,
        help=(
            "Cap on NEW Claude calls this run (the AI-read step's dominant, previously-"
            "ungoverned runtime cost). Unbounded by default -- unchanged behavior. Cards with "
            "no stored read are filled before cards that only need a refresh; anything the "
            "cap does not reach becomes eligible again next run."
        ),
    )
    args = parser.parse_args(argv)
    if args.max_reads is not None and args.max_reads < 0:
        parser.error("--max-reads must be 0 or greater")
    schema = "public" if args.target == "prod" else args.target

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

    client = create_client(url, key, options=SyncClientOptions(schema=schema))

    # Slice 5b: fill ai_read / read_model for changed cards only. Skipped when no
    # ANTHROPIC_API_KEY (verdicts still upsert, as in 5a) so the pipeline degrades
    # gracefully and the secret is a soft dependency.
    if os.getenv("ANTHROPIC_API_KEY"):
        existing = _fetch_existing_assessments(client)
        rows_by_key = {
            (r["market_code"], r["ticker"]): r for r in _latest_per_ticker(rows)
        }
        summary = attach_reads(
            records, rows_by_key, existing, anthropic.Anthropic(), max_reads=args.max_reads
        )
        print(
            "generate_assessments: reads "
            f"generated={summary['generated']} carried={summary['carried']} "
            f"capped={summary['capped']} failed={summary['failed']}"
        )
    else:
        print(
            "generate_assessments: no ANTHROPIC_API_KEY, skipping prose reads (verdicts only)"
        )

    _upsert_records(client, records)

    print(f"generate_assessments: upserted {len(records)} rows in '{schema}'")
    return 0


if __name__ == "__main__":
    sys.exit(main())
