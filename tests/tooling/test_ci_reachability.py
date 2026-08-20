"""Pins for .gitlab-ci.yml traps that no static check catches.

Adapted from the migrate-to-gitlab skill's template for this repo. Two things differ from
the template on purpose:

  - No `id_tokens` / WIF pin. This repo authenticates to Supabase with a plain service-role
    key (a CI/CD variable), not GCP Workload Identity Federation — there is no OIDC token
    exchange here for a test to protect. Carrying the pin anyway would pass vacuously
    (nothing in this file ever sets `id_tokens:`), which is exactly the kind of pin the
    skill warns against keeping.

  - No "deploy job reachable only by deliberate dispatch" pin. The skill's original repo had
    a `when: manual` deploy job reachable from every MR — a real defect once. This repo has
    no `stage: deploy` job at all (Render redeploys itself by watching the repo; nothing in
    this file publishes anything), so there is nothing for that pin to assert. Forcing a
    `deploy_jobs` list to be non-empty would fail this file the moment it's copied in, for a
    risk that doesn't exist here.

  - `EXPENSIVE_COMMAND` targets the two things this repo can lose money or corrupt data on —
    a Supabase write (`apply_supabase_migrations.py`, `export_to_supabase.py`) or a paid
    Anthropic call (`generate_assessments.py` without `--dry-run`) — not `dbt build`. dbt
    only ever writes to an ephemeral, job-local DuckDB file here; the CI-fixture `dbt build`
    in `validate:full` is cheap and idempotent, unlike the BigQuery original this template
    came from.

WHY THIS FILE EXISTS: `glab ci lint` passing, the YAML parsing, and a green pipeline all
coexisted with three real defects in the migration this template came from — a deploy button
on every merge request, jobs that would die at an auth guard on every run, and a nightly
schedule that would have started a second full production build every night. This repo's
own equivalent of that last one is concrete: `data-pipeline` already calls
`apply_supabase_migrations.py` on its weekly cron, so an incorrectly-guarded
`supabase-migrate` would apply migrations to production a second time, concurrently, on
every schedule. These tests evaluate `rules:` the way GitLab does, which is the only thing
that would have caught it.

TWO RULES FOR EXTENDING THIS FILE:

  1. Assert the PROPERTY, never the spelling. A pin on rule position breaks the moment a job
     becomes correctly guarded a different way, and a correct job failing a test for no
     reason is how pins get deleted.

  2. Verify a new test FAILS against the broken form before accepting it. A pin that has
     never fired is not a pin. (Both tests below were run by hand against a deliberately
     broken .gitlab-ci.yml — schedule guard removed, web rule changed to a bare
     `when: manual` — and both failed with the expected message before this file was kept.)
"""

from __future__ import annotations

import pathlib
import re

import yaml

# --------------------------------------------------------------------------- #
# CONFIG
# --------------------------------------------------------------------------- #

# tests/tooling/test_ci_reachability.py -> parents[0]=tooling, [1]=tests, [2]=repo root.
CI_FILE = pathlib.Path(__file__).resolve().parents[2] / ".gitlab-ci.yml"

# The ONLY job a scheduled pipeline may reach.
SCHEDULED_JOB: str = "data-pipeline"

# Real money / real production data, matched in COMMAND POSITION (start of line or after a
# shell separator) so `cd x && python scripts/export_to_supabase.py ...` is still caught.
# Excludes any invocation carrying `--dry-run` on the same line — validate:full's smoke test
# of generate_assessments.py must not count as a production write.
EXPENSIVE_COMMAND = re.compile(
    r"(?m)(?:^|&&|;|\|)\s*(?:cd \S+\s*&&\s*)*"
    r"python\s+scripts/(?:apply_supabase_migrations|export_to_supabase|generate_assessments)\.py\b"
    r"(?![^\n]*--dry-run)"
)

# Vacuity guard: below this many recognised jobs, the detector has probably stopped seeing
# them and the test passes for the wrong reason. Two, not three: this repo has exactly two
# jobs that ever touch production (supabase-migrate, data-pipeline), not the BigQuery
# original's larger fleet of build jobs.
MIN_EXPENSIVE_JOBS = 2

# Narrowing a rule must not disable work that has to stay automatic: supabase-migrate must
# still apply migrations on an ordinary push to main, not just on manual dispatch.
MUST_STAY_AUTOMATIC = {"supabase-migrate": "push_main"}

# --------------------------------------------------------------------------- #
# Rule evaluation — how GitLab actually resolves `rules:`
# --------------------------------------------------------------------------- #

# `$CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH` is true in three pipeline contexts at once
# (schedule, web, push_main) — that single fact is what makes the schedule trap possible.
# `changes:` is evaluated as TRUE on any pipeline that is not a push or an MR, so it is
# deliberately ignored below: modelling it as a filter would hide the exact bug these tests
# exist to catch.
_CONDITION_TRUTH = {
    '$CI_PIPELINE_SOURCE == "schedule"': {"schedule"},
    '$CI_PIPELINE_SOURCE == "web"': {"web"},
    '$CI_PIPELINE_SOURCE == "merge_request_event"': {"mr"},
    "$CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH": {"schedule", "web", "push_main"},
    '$CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH && $CI_PIPELINE_SOURCE == "push"': {"push_main"},
}


def _ci() -> dict:
    return yaml.safe_load(CI_FILE.read_text(encoding="utf-8"))


def _jobs(ci: dict) -> dict:
    """Real jobs only — not anchors (`.name`) and not top-level config."""
    return {
        k: v
        for k, v in ci.items()
        if not k.startswith(".") and isinstance(v, dict) and "script" in v
    }


def _ci_cond(rule: dict) -> str | None:
    """Normalise a rule's `if:` — quote style and whitespace only, never semantics."""
    cond = rule.get("if")
    return None if cond is None else " ".join(cond.replace("'", '"').split())


def _matches(cond: str | None, context: str) -> bool:
    """Does this condition hold in `context`? An UNRECOGNISED condition RAISES.

    Never assume an unknown condition is false. Treating unknown as "does not match" is how
    a guard test quietly stops guarding: someone writes an equivalent condition a different
    way, the recogniser shrugs, and a job that DOES run is reported safe.
    """
    if cond is None:
        return True  # a rule with no `if:` always matches
    if cond in _CONDITION_TRUTH:
        return context in _CONDITION_TRUTH[cond]
    raise AssertionError(
        f"unrecognised CI rule condition {cond!r}. These tests reason about pipeline "
        f"reachability by classifying conditions, and an unknown one must not be assumed "
        f"harmless. Add it to _CONDITION_TRUTH, deciding deliberately which of "
        f"schedule/web/mr/push_main it holds in."
    )


def _when_in(job: dict, context: str) -> str:
    """The effective `when:` for `job` in `context` — first match wins, else never."""
    for rule in job.get("rules") or [{}]:
        if _matches(_ci_cond(rule), context):
            return rule.get("when", "on_success")
    return "never"


# --------------------------------------------------------------------------- #
# The pins
# --------------------------------------------------------------------------- #


def test_a_web_dispatch_never_auto_starts_production_work():
    """Asking for one manual job must not silently start a production write.

    A manual dispatch runs on the default branch. Clicking "run pipeline" to trigger, say, a
    validate-only check must never also start a Supabase migration or an Anthropic-billed
    assessment run. A web dispatch may OFFER production work as a button; it may not start it.
    """
    ci = _ci()
    checked = 0
    for name, job in _jobs(ci).items():
        if not any(EXPENSIVE_COMMAND.search(step) for step in (job.get("script") or [])):
            continue
        checked += 1
        assert _when_in(job, "web") in ("manual", "never"), (
            f"job {name!r} AUTO-STARTS on a web dispatch and touches production "
            f"(when={_when_in(job, 'web')!r}). Make it `when: manual`. "
            f"rules={job.get('rules')!r}"
        )

    assert checked >= MIN_EXPENSIVE_JOBS, (
        f"only {checked} production-writing jobs recognised — EXPENSIVE_COMMAND has "
        f"probably stopped seeing them, which makes this test pass vacuously"
    )

    # And the other direction, or the check above is satisfiable by disabling everything.
    for name, context in MUST_STAY_AUTOMATIC.items():
        assert _when_in(ci[name], context) == "on_success", (
            f"{name!r} no longer runs automatically on a {context} pipeline. Narrowing was "
            f"meant to affect web dispatches only."
        )


def test_only_the_scheduled_job_runs_on_a_schedule():
    """A scheduled pipeline must fire data-pipeline and NOTHING else.

    This is the most expensive mistake available in this file, and it fails SILENTLY — no
    job turns red, Supabase just gets migrated twice concurrently. A scheduled pipeline runs
    on the default branch, so it satisfies every `$CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH`
    rule in the file, including supabase-migrate's push-to-main clause.

    Rules are first-match-wins, so a guard is only a guard if it comes first.
    """
    ci = _ci()
    jobs = _jobs(ci)

    for name, job in jobs.items():
        if name == SCHEDULED_JOB:
            continue
        assert _when_in(job, "schedule") == "never", (
            f"job {name!r} WILL RUN on a scheduled pipeline. A schedule runs on the default "
            f"branch, so `$CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH` matches. Put the schedule "
            f"guard FIRST, or scope the job to an explicit source. rules={job.get('rules')!r}"
        )

    assert SCHEDULED_JOB in jobs, f"{SCHEDULED_JOB!r} is missing — the schedule has nothing to run"
    assert _when_in(jobs[SCHEDULED_JOB], "schedule") != "never", (
        f"{SCHEDULED_JOB!r} does not run on a schedule — the weekly refresh would never fire"
    )


def test_production_jobs_never_reachable_on_a_merge_request():
    """supabase-migrate and data-pipeline must never appear as jobs on an MR pipeline.

    Unlike the skill's original repo, this one has no separate `deploy` stage to pin — but
    the equivalent risk exists: a production-writing job reachable from an ordinary merge
    request, rather than only from a push to main, a schedule, or a deliberate web dispatch.
    """
    ci = _ci()
    jobs = _jobs(ci)
    production_jobs = [k for k, v in jobs.items() if v.get("stage") == "production"]
    assert production_jobs, "no production-stage jobs found — this test has gone stale"

    for name in production_jobs:
        assert _when_in(jobs[name], "mr") == "never", (
            f"job {name!r} is reachable on a merge-request pipeline "
            f"(when={_when_in(jobs[name], 'mr')!r}) — it would run against production on "
            f"every MR. rules={jobs[name].get('rules')!r}"
        )
