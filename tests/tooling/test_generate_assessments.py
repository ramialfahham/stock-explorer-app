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
        verdict_meaning: str | None = "healthy",
        content: list | None = None,
        stop_reason: str = "tool_use",
    ) -> None:
        if content is None:
            payload = {
                "read": text,
                "referenced_metrics": referenced_metrics or [],
                "verdict_meaning": verdict_meaning,
            }
            content = [_FakeToolUseBlock(payload)]
        self.content = content
        self.model = model
        self.stop_reason = stop_reason


_MEANING_WORDS = ("healthy", "mixed", "fragile")


class _FakeMessages:
    def __init__(self, text: str = "A steady read, financially healthy on these figures.",
                 model: str = "claude-haiku-4-5",
                 fail_calls: set[int] = frozenset(),
                 referenced_metrics: list | None = None,
                 verdict_meaning: str | None = "healthy",
                 content: list | None = None,
                 stop_reason: str = "tool_use",
                 auto_verdict_meaning: bool = False) -> None:
        self._text = text
        self._model = model
        self._fail_calls = set(fail_calls)
        self._referenced_metrics = referenced_metrics
        self._verdict_meaning = verdict_meaning
        self._content = content
        self._stop_reason = stop_reason
        # Opt-in only: a run over several real cards with DIFFERENT verdicts (e.g. main() end
        # to end against a real mart) needs a response that actually agrees with what each
        # individual call asked for, like the real API does -- a single static text/meaning
        # would legitimately fail the new meaning-matches-verdict check for every card except
        # the one it happens to match. Every other test uses one fixed verdict per fake client
        # and does not need this.
        self._auto_verdict_meaning = auto_verdict_meaning
        self.calls: list[dict] = []

    def create(self, **kwargs):
        idx = len(self.calls)
        self.calls.append(kwargs)
        if idx in self._fail_calls:
            raise RuntimeError("boom")
        text = self._text
        verdict_meaning = self._verdict_meaning
        if self._auto_verdict_meaning:
            user_content = next(
                (m.get("content", "") for m in kwargs.get("messages", []) if m.get("role") == "user"),
                "",
            )
            verdict_meaning = next(
                (w for w in _MEANING_WORDS if w in str(user_content).lower()), "healthy"
            )
            text = f"A steady read, financially {verdict_meaning} on these figures."
        return _FakeMessage(
            text, self._model, self._referenced_metrics,
            verdict_meaning=verdict_meaning,
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
    client = _FakeAnthropic(text="Sturdy, financially healthy on these figures.")
    summary = gen.attach_reads([rec], {("us_sp500", "OPX"): _metric_row()}, {}, client)
    assert summary == {"generated": 1, "carried": 0, "capped": 0, "failed": 0}
    assert rec["ai_read"] == "Sturdy, financially healthy on these figures."
    assert rec["read_model"] == "claude-haiku-4-5"
    assert len(client.messages.calls) == 1


def test_attach_reads_carries_forward_unchanged() -> None:
    rec = _base_record(input_hash="h1")
    existing = {("us_sp500", "OPX"): {"input_hash": "h1", "ai_read": "old read", "read_model": "m"}}
    client = _FakeAnthropic()
    summary = gen.attach_reads([rec], {("us_sp500", "OPX"): _metric_row()}, existing, client)
    assert summary == {"generated": 0, "carried": 1, "capped": 0, "failed": 0}
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
    client = _FakeAnthropic(text="ok read, financially healthy on these figures.", fail_calls={0})  # first card's call raises
    summary = gen.attach_reads([a, b], rows, {}, client)
    assert summary == {"generated": 1, "carried": 0, "capped": 0, "failed": 1}
    assert "ai_read" not in a                     # nothing was stored, nothing to clear
    assert b["ai_read"] == "ok read, financially healthy on these figures."   # the batch kept going


def test_attach_reads_clears_a_stale_read_when_its_regeneration_attempt_fails() -> None:
    """A card WITH an existing (now stale, hash-changed) read whose regeneration attempt
    fails must not keep showing that old prose under this run's fresh verdict -- same
    equity-analyst-reviewer finding as the cap case, different trigger."""
    rec = _base_record(input_hash="h2")
    existing = {("us_sp500", "OPX"): {"input_hash": "h1", "ai_read": "old", "read_model": "m"}}
    client = _FakeAnthropic(fail_calls={0})
    summary = gen.attach_reads([rec], {("us_sp500", "OPX"): _metric_row()}, existing, client)
    assert summary == {"generated": 0, "carried": 0, "capped": 0, "failed": 1}
    assert rec["ai_read"] is None
    assert rec["read_model"] is None


def test_attach_reads_logs_every_card_not_just_failures(capsys) -> None:
    """issue #22: a silent success and a card that was never even bucketed looked
    identical in the job log, which is what made that investigation need a live manual
    repro instead of just reading the log. Every bucket now prints its own ticker."""
    carried_rec = _base_record(ticker="CARRIED", input_hash="h1")
    generated_rec = _base_record(ticker="GENERATED")
    capped_rec = _base_record(ticker="CAPPED")
    existing = {
        ("us_sp500", "CARRIED"): {"input_hash": "h1", "ai_read": "old", "read_model": "m"},
    }
    rows = {
        ("us_sp500", "CARRIED"): _metric_row("CARRIED"),
        ("us_sp500", "GENERATED"): _metric_row("GENERATED"),
        ("us_sp500", "CAPPED"): _metric_row("CAPPED"),
    }
    client = _FakeAnthropic(text="ok read, financially healthy on these figures.")
    # order matters: no_stored_read before needs_refresh, so GENERATED (no stored read)
    # is attempted and CAPPED (also no stored read) is the one the cap does not reach.
    summary = gen.attach_reads(
        [carried_rec, generated_rec, capped_rec], rows, existing, client, max_reads=1
    )
    assert summary == {"generated": 1, "carried": 1, "capped": 1, "failed": 0}
    out = capsys.readouterr().out
    assert "carried for us_sp500/CARRIED" in out
    assert "generated for us_sp500/GENERATED" in out
    assert "capped for us_sp500/CAPPED" in out


def test_attach_reads_logs_a_missing_mart_row(capsys) -> None:
    """The defensive branch (records derive from the same rows as rows_by_key, so this
    "shouldn't happen") was previously silent -- indistinguishable from a genuine silent
    success in the log. Now logged like any other failure, with its ticker."""
    rec = _base_record()
    client = _FakeAnthropic()
    summary = gen.attach_reads([rec], {}, {}, client)  # rows_by_key has no matching row
    assert summary == {"generated": 0, "carried": 0, "capped": 0, "failed": 1}
    assert client.messages.calls == []
    err = capsys.readouterr().err
    assert "us_sp500/OPX" in err
    assert "no matching mart row" in err


def test_main_max_reads_negative_is_rejected() -> None:
    """Rejected by argparse itself, before any file/credential access -- no duckdb/env setup
    needed here."""
    try:
        gen.main(["--max-reads", "-1"])
    except SystemExit as exc:
        assert exc.code == 2  # argparse's own error exit code
    else:
        raise AssertionError("expected SystemExit from parser.error on a negative --max-reads")


def test_attach_reads_negative_max_reads_is_clamped_to_fully_capped() -> None:
    """Defense in depth for attach_reads() itself, called directly (not through main()'s CLI
    guard): Python slicing treats a negative stop index as "count back from the end", so an
    unguarded new_first[:-1] on a typo would keep nearly everything -- the opposite of what
    the cap exists to prevent."""
    rec = _base_record()
    client = _FakeAnthropic()
    summary = gen.attach_reads([rec], {("us_sp500", "OPX"): _metric_row()}, {}, client, max_reads=-1)
    assert summary == {"generated": 0, "carried": 0, "capped": 1, "failed": 0}
    assert client.messages.calls == []


# --- --max-reads: bounds new Claude calls per run with a per-run cap. Cards with no stored
# read are filled before cards that only need a refresh -- a bare fallback line is a worse
# gap than a stale read -- and whatever a tight cap can't reach this run is left exactly like
# `carried` (keys absent), so it retries on the next run rather than being lost.


def test_max_reads_none_is_unbounded_default() -> None:
    """Omitting --max-reads must not change today's behavior at all."""
    a = _base_record(ticker="AAA")
    b = _base_record(ticker="BBB")
    rows = {("us_sp500", "AAA"): _metric_row("AAA"), ("us_sp500", "BBB"): _metric_row("BBB")}
    client = _FakeAnthropic(text="ok read, financially healthy on these figures.")
    summary = gen.attach_reads([a, b], rows, {}, client)
    assert summary == {"generated": 2, "carried": 0, "capped": 0, "failed": 0}


def test_max_reads_caps_new_calls_and_reports_capped() -> None:
    a = _base_record(ticker="AAA")
    b = _base_record(ticker="BBB")
    c = _base_record(ticker="CCC")
    rows = {
        ("us_sp500", "AAA"): _metric_row("AAA"),
        ("us_sp500", "BBB"): _metric_row("BBB"),
        ("us_sp500", "CCC"): _metric_row("CCC"),
    }
    client = _FakeAnthropic(text="ok read, financially healthy on these figures.")
    summary = gen.attach_reads([a, b, c], rows, {}, client, max_reads=2)
    assert summary == {"generated": 2, "carried": 0, "capped": 1, "failed": 0}
    assert len(client.messages.calls) == 2
    # deterministic: the records' own relative order decides who gets skipped, not
    # something that could vary run to run.
    assert "ai_read" in a and "ai_read" in b
    assert "ai_read" not in c


def test_max_reads_prioritizes_cards_with_no_stored_read_over_refreshes() -> None:
    """A refresh candidate (a read already exists, only input_hash changed) must not steal
    the run's budget from a card that has never had a read at all -- the fallback badge-only
    state is the worse gap. Order in the input list is deliberately the opposite of the
    expected priority, so this fails against an implementation that just takes records in
    list order."""
    stale = _base_record(ticker="STALE", input_hash="h2")  # refresh candidate, listed FIRST
    fresh = _base_record(ticker="FRESH", input_hash="h1")  # no stored read at all
    rows = {
        ("us_sp500", "STALE"): _metric_row("STALE"),
        ("us_sp500", "FRESH"): _metric_row("FRESH"),
    }
    existing = {("us_sp500", "STALE"): {"input_hash": "h1", "ai_read": "old", "read_model": "m"}}
    client = _FakeAnthropic(text="ok read, financially healthy on these figures.")
    summary = gen.attach_reads([stale, fresh], rows, existing, client, max_reads=1)
    assert summary == {"generated": 1, "carried": 0, "capped": 1, "failed": 0}
    assert fresh["ai_read"] == "ok read, financially healthy on these figures."  # no-stored-read card wins the slot...
    # ...the refresh is deferred; its stale H1 read is explicitly cleared, not left showing
    # under this run's fresh verdict (equity-analyst-reviewer finding: the frontend's own
    # staleness guard checks snapshot_date, not input_hash, so it can't catch this itself).
    assert stale["ai_read"] is None
    assert stale["read_model"] is None


def test_max_reads_zero_generates_nothing_but_still_reports_the_gap() -> None:
    rec = _base_record()
    client = _FakeAnthropic()
    summary = gen.attach_reads([rec], {("us_sp500", "OPX"): _metric_row()}, {}, client, max_reads=0)
    assert summary == {"generated": 0, "carried": 0, "capped": 1, "failed": 0}
    assert client.messages.calls == []


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
    assert summary == {"generated": 0, "carried": 0, "capped": 0, "failed": 1}
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
    assert summary == {"generated": 1, "carried": 0, "capped": 0, "failed": 0}
    assert rec["ai_read"] == "Operating margin looks strong, financially healthy on these figures."


def test_attach_reads_rejects_a_style_violation(capsys) -> None:
    """The style guard's own reason to exist: text that fails find_read_style_violations is
    treated exactly like a hallucination-guard rejection -- fails closed, same "failed" count,
    same self-healing path, no separate return-value shape."""
    rec = _base_record()
    client = _FakeAnthropic(text="This is a great buy right now! Financially healthy on these figures.")
    summary = gen.attach_reads([rec], {("us_sp500", "OPX"): _metric_row()}, {}, client)
    assert summary == {"generated": 0, "carried": 0, "capped": 0, "failed": 1}
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
    assert summary == {"generated": 1, "carried": 0, "capped": 0, "failed": 0}
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
    client = _FakeAnthropic(text="This is a great buy right now! Financially healthy on these figures.")  # style-dirty, metric-clean
    summary = gen.attach_reads([rec], {("us_sp500", "OPX"): _metric_row()}, {}, client)
    assert summary == {"generated": 1, "carried": 0, "capped": 0, "failed": 0}
    assert rec["ai_read"] == "This is a great buy right now! Financially healthy on these figures."


def test_attach_reads_rejects_a_response_with_no_tool_use_block(capsys) -> None:
    """The model ignoring tool_choice (a stop_reason/SDK-version change) must fail closed
    exactly like every other rejection, not be swallowed silently -- the whole point of this
    guard is that a real pipeline run can tell WHY a card came back unread."""
    rec = _base_record()
    client = _FakeAnthropic(content=[_FakeTextBlock()], stop_reason="end_turn")
    summary = gen.attach_reads([rec], {("us_sp500", "OPX"): _metric_row()}, {}, client)
    assert summary == {"generated": 0, "carried": 0, "capped": 0, "failed": 1}
    assert "ai_read" not in rec and "read_model" not in rec
    assert "no tool_use block" in capsys.readouterr().err


def test_attach_reads_rejects_a_blank_read(capsys) -> None:
    rec = _base_record()
    client = _FakeAnthropic(text="   ")
    summary = gen.attach_reads([rec], {("us_sp500", "OPX"): _metric_row()}, {}, client)
    assert summary == {"generated": 0, "carried": 0, "capped": 0, "failed": 1}
    assert "ai_read" not in rec and "read_model" not in rec
    assert "malformed tool payload" in capsys.readouterr().err


def test_attach_reads_rejects_non_list_referenced_metrics(capsys) -> None:
    rec = _base_record()
    client = _FakeAnthropic(text="Operating margin looks strong.", referenced_metrics="oops")
    summary = gen.attach_reads([rec], {("us_sp500", "OPX"): _metric_row()}, {}, client)
    assert summary == {"generated": 0, "carried": 0, "capped": 0, "failed": 1}
    assert "ai_read" not in rec and "read_model" not in rec
    assert "malformed tool payload" in capsys.readouterr().err


def test_attach_reads_rejects_a_non_string_verdict_meaning(capsys) -> None:
    """Mirrors test_attach_reads_rejects_non_list_referenced_metrics -- verdict_meaning has
    the same malformed-payload guard (not isinstance(..., str)) as referenced_metrics'
    not isinstance(..., list) on the same line, and needs the same direct coverage: a
    future edit dropping just this one clause would otherwise pass every other test."""
    rec = _base_record()
    client = _FakeAnthropic(
        text="Operating margin looks strong, financially healthy on these figures.",
        verdict_meaning=None,
    )
    summary = gen.attach_reads([rec], {("us_sp500", "OPX"): _metric_row()}, {}, client)
    assert summary == {"generated": 0, "carried": 0, "capped": 0, "failed": 1}
    assert "ai_read" not in rec and "read_model" not in rec
    assert "malformed tool payload" in capsys.readouterr().err


# --- _upsert_records: batches grouped by key-shape. A single upsert call mixing "carried"
# (omits ai_read/read_model) and "generated" (includes them) records nulls the carried ones'
# stored reads, because PostgREST's `columns` param is the union of keys across the WHOLE
# call, not per-row.


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


def test_a_capped_cards_cleared_read_and_a_generated_cards_fresh_read_both_survive_the_same_upsert_call() -> None:
    """Pins the one composition path the two source features (--max-reads and !149's
    upsert-clobbering fix) never got reviewed together: attach_reads() explicitly nulls a
    capped/failed card's stale ai_read (_clear_stale_read_if_present), which gives it the
    SAME key-shape (ai_read/read_model present, just None) as a genuinely generated card --
    so _upsert_records() batches them together. That must not reopen the exact bug !149
    fixed: neither record's write may bleed into the other's."""
    existing = [
        {"market_code": "us_sp500", "ticker": "STALE", "input_hash": "h1",
         "ai_read": "old stored read.", "read_model": "claude-haiku-4-5"},
    ]
    stale = _base_record(ticker="STALE", input_hash="h2")   # hash changed -> needs_refresh
    fresh = _base_record(ticker="FRESH", input_hash="h1")   # no stored read -> no_stored_read
    rows = {
        ("us_sp500", "STALE"): _metric_row("STALE"),
        ("us_sp500", "FRESH"): _metric_row("FRESH"),
    }
    existing_by_key = {("us_sp500", "STALE"): existing[0]}
    client = _FakeAnthropic(text="fresh read, financially healthy on these figures.")
    summary = gen.attach_reads([stale, fresh], rows, existing_by_key, client, max_reads=1)
    assert summary == {"generated": 1, "carried": 0, "capped": 1, "failed": 0}
    assert stale["ai_read"] is None and stale["read_model"] is None  # cleared, not absent
    assert fresh["ai_read"] == "fresh read, financially healthy on these figures."

    fake_sb = _FakeSupabase(existing=existing)
    calls = gen._upsert_records(fake_sb, [stale, fresh])
    assert calls == 1  # same key-shape (both carry ai_read/read_model) -> one call
    assert fake_sb.postgrest_state[("us_sp500", "STALE")]["ai_read"] is None
    assert fake_sb.postgrest_state[("us_sp500", "FRESH")]["ai_read"] == "fresh read, financially healthy on these figures."


def test_upsert_records_batches_within_each_key_shape_group() -> None:
    """batch_size still applies inside each key-shape group, not just across the whole
    record set."""
    records = [_base_record(ticker=f"T{i}") for i in range(5)]  # all same shape
    fake_sb = _FakeSupabase(existing=[])
    calls = gen._upsert_records(fake_sb, records, batch_size=2)
    assert calls == 3  # 2 + 2 + 1
    assert sum(len(b) for b in fake_sb.upserts) == 5


# --- _fetch_existing_assessments: paginates past PostgREST's default row cap -- an
# unranged select silently truncates past that many rows, so every card past the cutoff
# looks permanently new every run.


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
    # _ROWS carries a real mix of verdicts (OPX/PREX red, FINX green), so a single static
    # response would fail the meaning-matches-verdict check for whichever cards it doesn't
    # happen to match -- auto_verdict_meaning replies in line with what each call actually
    # asked for, the same way the real API does.
    monkeypatch.setattr(
        gen.anthropic,
        "Anthropic",
        lambda *a, **k: _FakeAnthropic(auto_verdict_meaning=True),
    )

    assert gen.main(["--duckdb-path", str(db)]) == 0
    upserted = [rec for batch in fake_sb.upserts for rec in batch]
    assert upserted
    for rec in upserted:
        assert "financially" in rec["ai_read"]
        assert rec["read_model"] == "claude-haiku-4-5"


def test_main_max_reads_flag_caps_the_run_end_to_end(tmp_path: Path, monkeypatch) -> None:
    """--max-reads threaded all the way from argv through to attach_reads: with 3 eligible
    cards (OPX/FINX/PREX in _ROWS) and a cap of 1, exactly one upserted row gets a fresh
    ai_read; the rest are left without the key, same as any other carried/capped card."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")
    monkeypatch.setenv("SUPABASE_URL", "https://x.supabase.co")
    monkeypatch.setenv("SUPABASE_SERVICE_ROLE_KEY", "svc")
    db = tmp_path / "mart.duckdb"
    _make_mart(db, _ROWS)

    fake_sb = _FakeSupabase(existing=[])
    monkeypatch.setattr(gen, "create_client", lambda url, key, options=None: fake_sb)
    # Same reasoning as test_main_with_anthropic_key_attaches_reads: _ROWS mixes verdicts,
    # so the single card this cap lets through needs a response matching whichever verdict
    # it actually is, not a fixed one that might not match.
    fake_client = _FakeAnthropic(auto_verdict_meaning=True)
    monkeypatch.setattr(gen.anthropic, "Anthropic", lambda *a, **k: fake_client)

    assert gen.main(["--duckdb-path", str(db), "--max-reads", "1"]) == 0
    upserted = [rec for batch in fake_sb.upserts for rec in batch]
    assert len(upserted) == 3
    with_read = [rec for rec in upserted if "ai_read" in rec]
    without_read = [rec for rec in upserted if "ai_read" not in rec]
    assert len(with_read) == 1
    assert len(without_read) == 2
    assert len(fake_client.messages.calls) == 1


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
