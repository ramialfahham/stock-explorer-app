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


def _make_mart(path: Path, rows: list[dict]) -> None:
    text_cols = {"market_code", "ticker", "company_type", "currency", "snapshot_date"}
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


class _FakeSupabaseTable:
    def __init__(self, store: "_FakeSupabase") -> None:
        self._store = store
        self._op: str | None = None
        self._batch = None

    def select(self, *_a, **_k) -> "_FakeSupabaseTable":
        self._op = "select"
        return self

    def upsert(self, batch, on_conflict=None) -> "_FakeSupabaseTable":
        self._op = "upsert"
        self._batch = batch
        return self

    def execute(self) -> _FakeResponse:
        if self._op == "select":
            return _FakeResponse(list(self._store.existing))
        if self._op == "upsert":
            self._store.upserts.append(self._batch)
        return _FakeResponse(None)


class _FakeSupabase:
    def __init__(self, existing: list[dict] | None = None) -> None:
        self.upserts: list[list[dict]] = []
        self.existing = existing or []

    def table(self, _name: str) -> _FakeSupabaseTable:
        return _FakeSupabaseTable(self)


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
        referenced_metrics=[{"label": "Operating margin", "value_as_shown": "99.9%"}],  # wrong
    )
    summary = gen.attach_reads([rec], {("us_sp500", "OPX"): _metric_row()}, {}, client)
    assert summary == {"generated": 0, "carried": 0, "failed": 1}
    assert "ai_read" not in rec and "read_model" not in rec


def test_attach_reads_accepts_a_read_citing_a_number_that_matches() -> None:
    rec = _base_record()
    client = _FakeAnthropic(
        text="Operating margin looks strong, financially healthy on these figures.",
        referenced_metrics=[{"label": "Operating margin", "value_as_shown": "24.0%"}],  # correct
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
    monkeypatch.setattr(gen, "create_client", lambda url, key: fake_sb)

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
    monkeypatch.setattr(gen, "create_client", lambda url, key: fake_sb)
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
