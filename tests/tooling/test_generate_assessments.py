"""Offline test for the assessment generator (Slice 5a) — no Supabase, no network."""

from __future__ import annotations

from pathlib import Path

import duckdb

import generate_assessments as gen
from assessment_rules import VERDICTS

_ROWS = [
    # operating, green (older snapshot)
    {"market_code": "us_sp500", "ticker": "OPX", "company_type": "operating", "currency": "USD",
     "snapshot_date": "2026-06-01", "net_debt_to_ebitda": 1.1, "ebit_margin_pct": 24.0, "fcf_margin_pct": 16.0},
    # SAME ticker, later snapshot, now red (fcf negative) -> dedupe must keep this one
    {"market_code": "us_sp500", "ticker": "OPX", "company_type": "operating", "currency": "USD",
     "snapshot_date": "2026-07-01", "net_debt_to_ebitda": 1.1, "ebit_margin_pct": 24.0, "fcf_margin_pct": -3.0},
    # financial, green
    {"market_code": "us_sp500", "ticker": "FINX", "company_type": "financial", "currency": "USD",
     "snapshot_date": "2026-07-01", "statement_roe_pct": 13.0, "net_margin_pct": 30.0, "roa_pct": 1.2},
    # pre_revenue, red (short runway) — non-USD to exercise currency-aware money amounts
    {"market_code": "jp_topix", "ticker": "PREX", "company_type": "pre_revenue", "currency": "JPY",
     "snapshot_date": "2026-07-01", "cash_runway_months": 8.0, "net_cash": 1.0e8,
     "working_capital": -5.0e7},
]

# Operating on the annual fallback: the card face labels its margin "(annual)", so the loader
# must carry ebit_margin_basis or the read names it "(TTM)" again.
_ANNUAL_BASIS_ROW = {
    "market_code": "us_sp500", "ticker": "ANNX", "company_type": "operating", "currency": "USD",
    "snapshot_date": "2026-07-01", "net_debt_to_ebitda": 0.9, "ebit_margin_pct": 12.3,
    "fcf_margin_pct": 5.0, "ebit_margin_basis": "annual_latest",
}


def _make_mart(path: Path, rows: list[dict]) -> None:
    text_cols = {
        "market_code", "ticker", "company_type", "currency", "snapshot_date", "ebit_margin_basis"
    }
    defs = ", ".join(
        f"{c} VARCHAR" if c in text_cols else f"{c} DOUBLE"
        for c in gen.ASSESSMENT_INPUT_COLUMNS
    )
    con = duckdb.connect(str(path))
    con.execute("create schema if not exists marts")
    con.execute(f"create table marts.mart_stock_cards ({defs})")
    for row in rows:
        cols = list(row.keys())
        placeholders = ", ".join("?" for _ in cols)
        con.execute(
            f"insert into marts.mart_stock_cards ({', '.join(cols)}) values ({placeholders})",
            [row[c] for c in cols],
        )
    con.close()


def test_build_records_dedupes_and_assigns_verdicts(tmp_path: Path) -> None:
    db = tmp_path / "mart.duckdb"
    _make_mart(db, _ROWS)
    records = gen.build_assessment_records(gen._load_mart_rows(db))

    by_ticker = {r["ticker"]: r for r in records}
    assert set(by_ticker) == {"OPX", "FINX", "PREX"}   # one record per (market, ticker)
    assert len(records) == 3                            # coverage: every eligible card gets a verdict

    # dedupe kept the latest snapshot (which flipped OPX to red)
    assert by_ticker["OPX"]["snapshot_date"] == "2026-07-01"
    assert by_ticker["OPX"]["health_verdict"] == "red"
    assert by_ticker["FINX"]["health_verdict"] == "green"
    assert by_ticker["PREX"]["health_verdict"] == "red"

    for rec in records:
        assert rec["health_verdict"] in VERDICTS
        assert "ai_read" not in rec and "read_model" not in rec  # 5a never writes/clobbers the read
        assert len(rec["input_hash"]) == 64
        assert set(rec) == {
            "market_code", "ticker", "company_type", "health_verdict",
            "input_hash", "snapshot_date", "generated_at",
        }


def test_loader_carries_the_margin_basis_into_the_read(tmp_path: Path) -> None:
    """Removing ebit_margin_basis from ASSESSMENT_INPUT_COLUMNS would make every annual-basis
    read say "(TTM)" beside a card that says "(annual)", with nothing else failing; this pins
    the column from DuckDB through to the prompt."""
    from assessment_rules import build_read_messages

    db = tmp_path / "mart.duckdb"
    _make_mart(db, [_ANNUAL_BASIS_ROW])
    rows = {r["ticker"]: r for r in gen._load_mart_rows(db)}
    assert rows["ANNX"]["ebit_margin_basis"] == "annual_latest"
    _system, user = build_read_messages(rows["ANNX"], "yellow")
    assert "- Operating margin (annual): 12.3%" in user
    assert "Operating margin (TTM)" not in user


def test_dry_run_needs_no_credentials(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.delenv("SUPABASE_URL", raising=False)
    monkeypatch.delenv("SUPABASE_SERVICE_ROLE_KEY", raising=False)
    db = tmp_path / "mart.duckdb"
    _make_mart(db, _ROWS)
    assert gen.main(["--duckdb-path", str(db), "--dry-run"]) == 0


def test_missing_duckdb_returns_error() -> None:
    assert gen.main(["--duckdb-path", "/no/such/mart.duckdb", "--dry-run"]) == 1


# --- Slice 5b: the Claude Haiku read path (fakes injected, no network) ---------
# The real call forces tool-use (READ_TOOL_SCHEMA), so the fake response carries a tool_use
# block with an .input dict, not a text block -- matching what _generate_read actually parses.

class _FakeToolUseBlock:
    def __init__(self, payload: dict) -> None:
        self.type = "tool_use"
        self.input = payload


class _FakeTextBlock:
    """Simulates a response that ignored tool_choice, e.g. a stop_reason/SDK-version change --
    the `tool_block is None` branch in _generate_read has no tool_use block to find."""

    def __init__(self, text: str = "(no tool call)") -> None:
        self.type = "text"
        self.text = text


class _FakeMessage:
    def __init__(
        self,
        text: str,
        model: str,
        referenced_metrics: list | None = None,
        *,
        content: list | None = None,
        stop_reason: str = "tool_use",
    ) -> None:
        if content is None:
            payload = {"read": text, "referenced_metrics": referenced_metrics or []}
            content = [_FakeToolUseBlock(payload)]
        self.content = content
        self.model = model
        self.stop_reason = stop_reason


class _FakeMessages:
    def __init__(self, text: str = "A steady read on these figures.", model: str = "claude-haiku-4-5",
                 fail_calls: set[int] = frozenset(),
                 referenced_metrics: list | None = None,
                 content: list | None = None,
                 stop_reason: str = "tool_use") -> None:
        self._text = text
        self._model = model
        self._fail_calls = set(fail_calls)
        self._referenced_metrics = referenced_metrics
        self._content = content
        self._stop_reason = stop_reason
        self.calls: list[dict] = []

    def create(self, **kwargs):
        idx = len(self.calls)
        self.calls.append(kwargs)
        if idx in self._fail_calls:
            raise RuntimeError("boom")
        return _FakeMessage(
            self._text, self._model, self._referenced_metrics,
            content=self._content, stop_reason=self._stop_reason,
        )


class _FakeAnthropic:
    def __init__(self, **kwargs) -> None:
        self.messages = _FakeMessages(**kwargs)


class _FakeResponse:
    def __init__(self, data) -> None:
        self.data = data


# Simulates PostgREST's own real default row cap on an UNRANGED select -- independent of
# whatever generate_assessments.py's client code does or doesn't ask for. Without this, the
# fake would silently hand back every row of `existing` regardless, and a pagination
# regression (deleting the .range() call) would slip straight past the tests below.
_POSTGREST_ROW_CAP = 1000


class _FakeSupabaseTable:
    def __init__(self, store: "_FakeSupabase") -> None:
        self._store = store
        self._op: str | None = None
        self._batch = None
        self._range: tuple[int, int] | None = None

    def select(self, *_a, **_k) -> "_FakeSupabaseTable":
        self._op = "select"
        return self

    def range(self, start: int, end: int) -> "_FakeSupabaseTable":
        self._range = (start, end)
        return self

    def upsert(self, batch, on_conflict=None) -> "_FakeSupabaseTable":
        self._op = "upsert"
        self._batch = batch
        return self

    def execute(self) -> _FakeResponse:
        if self._op == "select":
            data = list(self._store.existing)
            if self._range is not None:
                start, end = self._range
                data = data[start : end + 1]
            else:
                data = data[:_POSTGREST_ROW_CAP]
            return _FakeResponse(data)
        if self._op == "upsert":
            self._store.upserts.append(self._batch)
            self._store.apply_upsert(self._batch)
        return _FakeResponse(None)


class _FakeSupabase:
    def __init__(self, existing: list[dict] | None = None) -> None:
        self.upserts: list[list[dict]] = []
        self.existing = existing or []
        # Simulates the REAL PostgREST behavior this fake used to ignore: a bulk upsert
        # call's `columns` query param is the union of keys across every record IN THAT ONE
        # CALL (postgrest-py's `_unique_columns`); a record omitting a column present
        # elsewhere in the same call gets it explicitly nulled, not left untouched. This is
        # what generate_assessments._upsert_records() exists to avoid -- postgrest_state is
        # what the database would actually end up holding after every upsert() call this
        # fake has seen, keyed the same way generate_assessments.py keys records.
        self.postgrest_state: dict[tuple, dict] = {
            (r["market_code"], r["ticker"]): dict(r) for r in self.existing
        }

    def table(self, _name: str) -> _FakeSupabaseTable:
        return _FakeSupabaseTable(self)

    def apply_upsert(self, batch: list[dict]) -> None:
        columns = {key for record in batch for key in record.keys()}
        for record in batch:
            key = (record["market_code"], record["ticker"])
            row = self.postgrest_state.setdefault(key, {})
            for column in columns:
                row[column] = record.get(column)  # missing -> None, matching real PostgREST


def _base_record(*, ticker: str = "OPX", input_hash: str = "h1", verdict: str = "green") -> dict:
    return {
        "market_code": "us_sp500", "ticker": ticker, "company_type": "operating",
        "health_verdict": verdict, "input_hash": input_hash,
        "snapshot_date": "2026-07-01", "generated_at": "2026-07-01T00:00:00+00:00",
    }


def _metric_row(ticker: str = "OPX") -> dict:
    return {
        "market_code": "us_sp500", "ticker": ticker, "company_type": "operating",
        "net_debt_to_ebitda": 1.1, "ebit_margin_pct": 24.0, "fcf_margin_pct": 16.0,
    }


def test_attach_reads_generates_for_new_card() -> None:
    rec = _base_record()
    client = _FakeAnthropic(text="Sturdy on these figures.")
    summary = gen.attach_reads([rec], {("us_sp500", "OPX"): _metric_row()}, {}, client)
    assert summary == {"generated": 1, "carried": 0, "failed": 0}
    assert rec["ai_read"] == "Sturdy on these figures."
    assert rec["read_model"] == "claude-haiku-4-5"
    assert len(client.messages.calls) == 1


def test_attach_reads_carries_forward_unchanged() -> None:
    rec = _base_record(input_hash="h1")
    existing = {("us_sp500", "OPX"): {"input_hash": "h1", "ai_read": "old read", "read_model": "m"}}
    client = _FakeAnthropic()
    summary = gen.attach_reads([rec], {("us_sp500", "OPX"): _metric_row()}, existing, client)
    assert summary == {"generated": 0, "carried": 1, "failed": 0}
    # keys left ABSENT so the upsert preserves the stored read (never clobbers)
    assert "ai_read" not in rec and "read_model" not in rec
    assert client.messages.calls == []


def test_attach_reads_regenerates_on_hash_change() -> None:
    rec = _base_record(input_hash="h2")
    existing = {("us_sp500", "OPX"): {"input_hash": "h1", "ai_read": "old", "read_model": "m"}}
    client = _FakeAnthropic(text="fresh read, financially healthy on these figures.")
    summary = gen.attach_reads([rec], {("us_sp500", "OPX"): _metric_row()}, existing, client)
    assert summary["generated"] == 1
    assert rec["ai_read"] == "fresh read, financially healthy on these figures."
    assert len(client.messages.calls) == 1


def test_attach_reads_regenerates_when_stored_read_null() -> None:
    rec = _base_record(input_hash="h1")
    existing = {("us_sp500", "OPX"): {"input_hash": "h1", "ai_read": None, "read_model": None}}
    client = _FakeAnthropic(text="filled in, financially healthy on these figures.")
    summary = gen.attach_reads([rec], {("us_sp500", "OPX"): _metric_row()}, existing, client)
    assert summary["generated"] == 1
    assert rec["ai_read"] == "filled in, financially healthy on these figures."


def test_attach_reads_isolates_a_failed_card() -> None:
    a = _base_record(ticker="AAA")
    b = _base_record(ticker="BBB")
    rows = {("us_sp500", "AAA"): _metric_row("AAA"), ("us_sp500", "BBB"): _metric_row("BBB")}
    client = _FakeAnthropic(text="ok read on these figures.", fail_calls={0})  # first card's call raises
    summary = gen.attach_reads([a, b], rows, {}, client)
    assert summary == {"generated": 1, "carried": 0, "failed": 1}
    assert "ai_read" not in a                     # failed card left null (retries next run)
    assert b["ai_read"] == "ok read on these figures."   # the batch kept going


def test_attach_reads_rejects_a_read_citing_a_number_that_does_not_match() -> None:
    """The hallucination guard's own reason to exist: a structured response whose
    referenced_metrics don't match the card's real data is treated exactly like an API
    failure -- fails closed, lands in the same "failed" count, no separate code path."""
    rec = _base_record()
    client = _FakeAnthropic(
        text="Operating margin looks strong.",
        referenced_metrics=[  # wrong
            {"label": "Operating margin (TTM)", "value_as_shown": "99.9%"}
        ],
    )
    summary = gen.attach_reads([rec], {("us_sp500", "OPX"): _metric_row()}, {}, client)
    assert summary == {"generated": 0, "carried": 0, "failed": 1}
    assert "ai_read" not in rec and "read_model" not in rec


def test_attach_reads_accepts_a_read_citing_a_number_that_matches() -> None:
    rec = _base_record()
    client = _FakeAnthropic(
        text="Operating margin looks strong, financially healthy on these figures.",
        referenced_metrics=[  # correct
            {"label": "Operating margin (TTM)", "value_as_shown": "24.0%"}
        ],
    )
    summary = gen.attach_reads([rec], {("us_sp500", "OPX"): _metric_row()}, {}, client)
    assert summary == {"generated": 1, "carried": 0, "failed": 0}
    assert rec["ai_read"] == "Operating margin looks strong, financially healthy on these figures."


def test_attach_reads_rejects_a_style_violation(capsys) -> None:
    """The style guard's own reason to exist: text that fails find_read_style_violations is
    treated exactly like a hallucination-guard rejection -- fails closed, same "failed" count,
    same self-healing path, no separate return-value shape."""
    rec = _base_record()
    client = _FakeAnthropic(text="This is a great buy right now!")
    summary = gen.attach_reads([rec], {("us_sp500", "OPX"): _metric_row()}, {}, client)
    assert summary == {"generated": 0, "carried": 0, "failed": 1}
    assert "ai_read" not in rec and "read_model" not in rec
    err = capsys.readouterr().err
    assert "style" in err.lower()
    assert "exclamation" in err.lower() or "investment-advice" in err.lower()


def test_attach_reads_accepts_a_style_clean_read() -> None:
    rec = _base_record()
    client = _FakeAnthropic(
        text="Operating margin is strong and debt is low, financially healthy on these figures."
    )
    summary = gen.attach_reads([rec], {("us_sp500", "OPX"): _metric_row()}, {}, client)
    assert summary == {"generated": 1, "carried": 0, "failed": 0}
    assert rec["ai_read"] is not None


def test_attach_reads_style_check_call_site_is_actually_wired(monkeypatch) -> None:
    """Mutation-style proof, matching test_operating_statement_roe_call_site_is_actually_wired
    in test_assessment_rules.py: neutralize find_read_style_violations at its _generate_read
    call site and confirm a style-violating-but-metric-clean read now SUCCEEDS. If this test
    passed even with the real check wired, that would prove nothing about the call site -- the
    point is that neutralizing it changes the outcome, so test_attach_reads_rejects_a_style_
    violation above is proven to depend on the real call site, not some other guard."""
    monkeypatch.setattr(gen, "find_read_style_violations", lambda read: [])
    rec = _base_record()
    client = _FakeAnthropic(text="This is a great buy right now!")  # style-dirty, metric-clean
    summary = gen.attach_reads([rec], {("us_sp500", "OPX"): _metric_row()}, {}, client)
    assert summary == {"generated": 1, "carried": 0, "failed": 0}
    assert rec["ai_read"] == "This is a great buy right now!"


def test_attach_reads_rejects_a_response_with_no_tool_use_block(capsys) -> None:
    """The model ignoring tool_choice (a stop_reason/SDK-version change) must fail closed
    exactly like every other rejection, not be swallowed silently -- the whole point of this
    guard is that a real pipeline run can tell WHY a card came back unread."""
    rec = _base_record()
    client = _FakeAnthropic(content=[_FakeTextBlock()], stop_reason="end_turn")
    summary = gen.attach_reads([rec], {("us_sp500", "OPX"): _metric_row()}, {}, client)
    assert summary == {"generated": 0, "carried": 0, "failed": 1}
    assert "ai_read" not in rec and "read_model" not in rec
    assert "no tool_use block" in capsys.readouterr().err


def test_attach_reads_rejects_a_blank_read(capsys) -> None:
    rec = _base_record()
    client = _FakeAnthropic(text="   ")
    summary = gen.attach_reads([rec], {("us_sp500", "OPX"): _metric_row()}, {}, client)
    assert summary == {"generated": 0, "carried": 0, "failed": 1}
    assert "ai_read" not in rec and "read_model" not in rec
    assert "malformed tool payload" in capsys.readouterr().err


def test_attach_reads_rejects_non_list_referenced_metrics(capsys) -> None:
    rec = _base_record()
    client = _FakeAnthropic(text="Operating margin looks strong.", referenced_metrics="oops")
    summary = gen.attach_reads([rec], {("us_sp500", "OPX"): _metric_row()}, {}, client)
    assert summary == {"generated": 0, "carried": 0, "failed": 1}
    assert "ai_read" not in rec and "read_model" not in rec
    assert "malformed tool payload" in capsys.readouterr().err


# --- _upsert_records: batches grouped by key-shape, root-caused against a real production
# incident (2026-09-15): a single upsert call mixing "carried" (omits ai_read/read_model)
# and "generated" (includes them) records nulled the carried ones' stored reads, because
# PostgREST's `columns` param is the union of keys across the WHOLE call, not per-row.


def test_fake_supabase_reproduces_the_real_clobbering_behavior() -> None:
    """Sanity check for the fake itself, pinning the OLD/broken shape (a single upsert()
    call for a mixed batch) so the fix's own test below has something real to fail
    against."""
    existing = [
        {"market_code": "us_sp500", "ticker": "CARRIED", "ai_read": "old stored read.",
         "read_model": "claude-haiku-4-5"},
    ]
    fake_sb = _FakeSupabase(existing=existing)
    carried = _base_record(ticker="CARRIED", input_hash="h1")  # omits ai_read/read_model
    generated = _base_record(ticker="GENERATED", input_hash="h1")
    generated["ai_read"] = "fresh read on these figures."
    generated["read_model"] = "claude-haiku-4-5"
    fake_sb.table("card_assessments").upsert(
        [carried, generated], on_conflict="market_code,ticker"
    ).execute()
    assert fake_sb.postgrest_state[("us_sp500", "CARRIED")]["ai_read"] is None  # clobbered


def test_upsert_records_does_not_clobber_a_carried_read_across_a_mixed_batch() -> None:
    """The fix: grouping by key-shape before chunking means a 'carried' record never shares
    an upsert call with a 'generated' one, so its stored read survives."""
    existing = [
        {"market_code": "us_sp500", "ticker": "CARRIED", "ai_read": "old stored read.",
         "read_model": "claude-haiku-4-5"},
    ]
    fake_sb = _FakeSupabase(existing=existing)
    carried = _base_record(ticker="CARRIED", input_hash="h1")
    generated = _base_record(ticker="GENERATED", input_hash="h1")
    generated["ai_read"] = "fresh read on these figures."
    generated["read_model"] = "claude-haiku-4-5"
    calls = gen._upsert_records(fake_sb, [carried, generated])
    assert calls == 2  # two distinct key-shapes -> two separate upsert calls
    stored = fake_sb.postgrest_state[("us_sp500", "CARRIED")]
    assert stored["ai_read"] == "old stored read."
    assert stored["read_model"] == "claude-haiku-4-5"
    assert fake_sb.postgrest_state[("us_sp500", "GENERATED")]["ai_read"] == "fresh read on these figures."


def test_upsert_records_batches_within_each_key_shape_group() -> None:
    """batch_size still applies inside each key-shape group, not just across the whole
    record set."""
    records = [_base_record(ticker=f"T{i}") for i in range(5)]  # all same shape
    fake_sb = _FakeSupabase(existing=[])
    calls = gen._upsert_records(fake_sb, records, batch_size=2)
    assert calls == 3  # 2 + 2 + 1
    assert sum(len(b) for b in fake_sb.upserts) == 5


# --- _fetch_existing_assessments: paginates past PostgREST's default row cap -- a single
# unranged select silently returned exactly 1000 of 1045 real rows on the 2026-09-15
# scheduled run, so every card past the cutoff looked permanently new every run.


def test_fetch_existing_assessments_paginates_past_the_default_row_cap() -> None:
    existing = [
        {"market_code": "us_sp500", "ticker": f"T{i}", "input_hash": "h",
         "ai_read": "r", "read_model": "m"}
        for i in range(gen._SELECT_PAGE_SIZE + 200)
    ]
    fake_sb = _FakeSupabase(existing=existing)
    result = gen._fetch_existing_assessments(fake_sb)
    assert len(result) == gen._SELECT_PAGE_SIZE + 200
    assert ("us_sp500", f"T{gen._SELECT_PAGE_SIZE + 199}") in result  # last row, past the old cutoff


def test_fetch_existing_assessments_single_page_when_under_the_cap() -> None:
    existing = [
        {"market_code": "us_sp500", "ticker": "OPX", "input_hash": "h", "ai_read": "r", "read_model": "m"}
    ]
    fake_sb = _FakeSupabase(existing=existing)
    result = gen._fetch_existing_assessments(fake_sb)
    assert result == {("us_sp500", "OPX"): existing[0]}


def test_main_without_anthropic_key_upserts_verdicts_only(tmp_path: Path, monkeypatch) -> None:
    # main() calls load_dotenv() itself, which would re-read a real local .env and defeat
    # delenv below — stub it out so this test can't reach the network with a real key.
    monkeypatch.setattr(gen, "load_dotenv", lambda *a, **k: None)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.setenv("SUPABASE_URL", "https://x.supabase.co")
    monkeypatch.setenv("SUPABASE_SERVICE_ROLE_KEY", "svc")
    db = tmp_path / "mart.duckdb"
    _make_mart(db, _ROWS)

    fake_sb = _FakeSupabase(existing=[])
    monkeypatch.setattr(gen, "create_client", lambda url, key, options=None: fake_sb)

    assert gen.main(["--duckdb-path", str(db)]) == 0
    upserted = [rec for batch in fake_sb.upserts for rec in batch]
    assert upserted  # verdicts still written
    for rec in upserted:  # but no LLM read attached without a key
        assert "ai_read" not in rec and "read_model" not in rec


def test_main_with_anthropic_key_attaches_reads(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")
    monkeypatch.setenv("SUPABASE_URL", "https://x.supabase.co")
    monkeypatch.setenv("SUPABASE_SERVICE_ROLE_KEY", "svc")
    db = tmp_path / "mart.duckdb"
    _make_mart(db, _ROWS)

    fake_sb = _FakeSupabase(existing=[])  # nothing stored -> every card regenerates
    monkeypatch.setattr(gen, "create_client", lambda url, key, options=None: fake_sb)
    monkeypatch.setattr(
        gen.anthropic,
        "Anthropic",
        lambda *a, **k: _FakeAnthropic(text="A steady read, financially healthy on these figures."),
    )

    assert gen.main(["--duckdb-path", str(db)]) == 0
    upserted = [rec for batch in fake_sb.upserts for rec in batch]
    assert upserted
    for rec in upserted:
        assert rec["ai_read"] == "A steady read, financially healthy on these figures."
        assert rec["read_model"] == "claude-haiku-4-5"


def _main_with_captured_options(tmp_path: Path, monkeypatch, argv: list[str]) -> object:
    monkeypatch.setattr(gen, "load_dotenv", lambda *a, **k: None)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.setenv("SUPABASE_URL", "https://x.supabase.co")
    monkeypatch.setenv("SUPABASE_SERVICE_ROLE_KEY", "svc")
    db = tmp_path / "mart.duckdb"
    _make_mart(db, _ROWS)
    seen = {}

    def fake_create_client(url, key, options=None):
        seen["options"] = options
        return _FakeSupabase(existing=[])

    monkeypatch.setattr(gen, "create_client", fake_create_client)
    assert gen.main(["--duckdb-path", str(db), *argv]) == 0
    return seen["options"]


def test_target_dev_passes_dev_schema_to_create_client(tmp_path: Path, monkeypatch) -> None:
    assert _main_with_captured_options(tmp_path, monkeypatch, ["--target", "dev"]).schema == "dev"


def test_target_prod_is_the_default_schema(tmp_path: Path, monkeypatch) -> None:
    assert _main_with_captured_options(tmp_path, monkeypatch, []).schema == "public"


def test_options_passed_to_create_client_is_the_sync_variant(tmp_path: Path, monkeypatch) -> None:
    """Same supabase-py==2.30.0 trap as export_to_supabase: the sync client reads
    options.storage, which only SyncClientOptions defines."""
    assert hasattr(_main_with_captured_options(tmp_path, monkeypatch, []), "storage")


def test_empty_anthropic_key_skips_reads(tmp_path: Path, monkeypatch) -> None:
    """dev-schema-check runs this script with ANTHROPIC_API_KEY set to the empty string so a
    manual dev write never spends on prose reads; empty must mean absent."""
    monkeypatch.setattr(gen, "load_dotenv", lambda *a, **k: None)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "")
    monkeypatch.setenv("SUPABASE_URL", "https://x.supabase.co")
    monkeypatch.setenv("SUPABASE_SERVICE_ROLE_KEY", "svc")
    db = tmp_path / "mart.duckdb"
    _make_mart(db, _ROWS)
    fake_sb = _FakeSupabase(existing=[])
    monkeypatch.setattr(gen, "create_client", lambda url, key, options=None: fake_sb)

    def no_client(*a, **k):
        raise AssertionError("Anthropic client constructed with an empty key")

    monkeypatch.setattr(gen.anthropic, "Anthropic", no_client)

    assert gen.main(["--duckdb-path", str(db)]) == 0
    assert all("ai_read" not in rec for batch in fake_sb.upserts for rec in batch)
