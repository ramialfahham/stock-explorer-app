# Working agreement — how the agent works here

> DURABLE. **Owns:** how an agent works here -- the protocol, task contracts, the review cycle,
> branch rules, decision rights, escalation.
> **Never:** project facts, metric definitions, or session state.

Read before doing anything. This governs how any AI agent (Claude Code, Cursor, …)
works in this repo.

## 1. The five-step protocol — Explore → Plan → Confirm → Implement → Verify

Every unit of work runs these five. **Confirm is a human checkpoint: wait for an
explicit "go" before editing files or running commands.**

- **Explore** — read-only; understand the code before proposing.
- **Plan** — write the task contract (`.claude/task/contract.md`).
- **Confirm** — state the plan back and WAIT for the user's go. Use plan mode so the
  harness enforces the wait. Weighing options or "what should I do?" is **not** a go.
- **Implement** — edit only files inside the contract's `scope_paths`.
- **Verify** — meet `done_when`, run the review cycle, then commit.

Exploring tradeoffs or being asked a question is not permission to change the repo.
Answer, recommend, then wait. When unsure, ask one short question instead of acting.
At the end of a session, update `.claude/active_work.md` so the next one continues cleanly.

## 2. The task contract + review cycle

Before a non-trivial change, write `.claude/task/contract.md` (template:
`CONTRACT_TEMPLATE.md`): objective, `scope_paths` (the files this task may touch),
`decisions_reserved` (owner-only questions — §6), `done_when`. Commit it with the
branch so it is visible in the MR. The scope-auditor reviewer flags any edit outside
`scope_paths` at review time.

Open work lives in GitLab Issues and Milestones, not prose docs. When a task has a GitLab
issue, `objective` links it (`Closes #N` / `Refs #N`) instead of restating the requirement
inline -- the issue is the single source for what and why; `contract.md` stays about
`scope_paths` and `done_when`. Reviewers check the diff against the linked issue's
`## What exactly` checklist, the same way they check it against `scope_paths`.

Before committing, run the review cycle (the commit gate enforces it):

1. Stage the paths the change touches, explicitly. Never `git add -A`: it sweeps whatever
   is untracked into a reviewed commit.
2. Run the reviewers the routing requires (`.claude/review_routing.json`) against the
   staged diff — cold, read-only, adversarial.
3. Write `.claude/task/review.md` (template: `REVIEW_TEMPLATE.md`) with each reviewer's
   verdict and the staged-diff hash.
4. `git commit` — blocked until the review matches the staged change, every required
   reviewer passed, and any escalation has a recorded answer.

Trace before you change a shared data model: know what depends on it downstream first.

**Prose earns its place only three ways.** Write it if it records a decision that cannot be
derived from the code, defines something the code cannot state itself (what a metric means,
what a contract guarantees), or is machine-checked (`scope_paths`, `diff_sha256`, verdicts).

NARRATIVE belongs in the commit message and the MR description, which are append-only and so
cannot rot into contradicting the current state. A contract or handover can rot, and did: MR
!115 spent six of its eleven review rounds on findings against narrative prose, after the code
it described had stopped changing. This is not licence to move a DECISION or an OPEN ITEM out
of `.claude/active_work.md`, though: that file is injected into the next session and an MR
description is not, so anything a future session must ACT on stays there.

Do not write a history of how the work went, a record of your
own mistakes, or a rationale in a file separate from the thing it explains. If a "why" is worth
keeping, put it next to the code, where a reviewer can check it against what it describes.

When you change a claim, grep the repo for the claim, not for the file you were told about.
Every one of those six rounds was the same failure: fixing the site a reviewer named and leaving
the same assertion standing elsewhere.

## 3. Branches

Every change goes on a new branch, never a commit or push to `main`. This repo lives on
GitLab, and only GitLab while the GitHub account remains suspended. That is conditional, not
permanent: revisit only if that account is recovered, and do not re-ask otherwise. **Do not add
an `origin` remote or push to one**: the GitHub account behind that name is suspended, and a
session pushed to it anyway despite this rule, which is why the remote was removed rather than
left in place with a warning.

Push to the `gitlab` remote with a FULL refspec (`git push gitlab <branch>:<branch>`)
and use `glab`, never `gh`. `git push gitlab <branch>` alone is not safe on this machine: the
global `~/.gitconfig` sets `push.default = upstream` and a branch's upstream can resolve to
`main`. Verify the push output's `-> <branch>` line names the feature branch.

Open an MR, wait for CI and the user's approval. **Never merge one** -- merging is the user's
action, every time, regardless of MR number. Before branching, check `glab mr list`: if the
work is a hard dependency of an open MR and a separate branch buys nothing, commit to that
branch instead.

Partly **hook-enforced**: a commit or push while on `main`/`master`, `git commit --amend` and
`--no-verify` are hard-blocked, and so is `gh pr merge`. **The merge guard matches `gh pr merge`
and nothing else** (`branch_discipline.py`'s `_GH_PR_MERGE` regex), so `glab mr merge` -- the
command this repo would actually reach for -- is NOT blocked by anything. Nothing stops you
there except this rule. Do not merge.

## 4. Quality

- **No hacky solutions.** If the clean way takes longer, say so — don't ship a workaround
  and call it done.
- **No unnecessary complexity.** Three clear lines beat a premature abstraction.
- **No scope creep.** Build exactly what was agreed; flag adjacent issues separately.
- **No half-finished work.** If it can't be done cleanly, say so before starting.
- **Tests are non-negotiable.** Output you can't eyeball must be covered by automated
  tests that run in CI.

## 5. Don't work against the user

- Never weaken config, scope, or cost/safety limits to "unblock" or finish faster without
  explicit confirmation in the same thread.
- Never silently narrow scope (doing part while implying the whole).
- When something blocks you, say so clearly and point at the relevant doc.

## 6. Decision rights — what the agent never decides alone

Each is the owner's call, escalated (§7) every time, however obvious it seems:

- Product/UX content, composition, ordering.
- Metric definitions, labels, formats; user-visible naming and wording.
- Anything permanent once published (URLs, slugs, public identifiers).
- A NEW mechanism (new dependency, service, lifecycle hook, framework, workflow step).
- Reinterpreting or extending a rule to a case it didn't cover.
- Changing an already-shipped output or number.
- Cost, schedule, scope (budget, run cadence, widening a task). Concretely, here: the agent
  spends nothing. No paid tier, no API token the owner did not ask for, no bought CI minutes,
  no self-hosted runner, no CI/CD variable VALUE, no protected-branch setting. A CI step that
  would call a paid API runs with the key emptied unless it is the scheduled production run.

Agent-executable = implementation already codified in a contract or standards doc.
**Meta-rule:** when a new case doesn't clearly match a written rule, the classification
itself is the owner's decision. "It's analogous to X" is not a licence.

## 7. Escalation

Before escalating, check your premises: list the assumptions behind the question and drop
any the written rules already answer. Then present **at least two conflicting paths with no
preferred option** — for each, what it implies, what it costs, what becomes hard later.
The owner decides; you inform.

## 8. Communication

Plain language, technically accurate. No filler, no motivational text, no emoji unless
asked. Backticks for files/functions/columns. Proposals proportional to the request. When
something goes wrong, say what happened, why, and the fix; do not bury it. A question for
the owner is plain language with context and a recommendation, and rare.

## Anti-patterns to hunt (extend with your own)

- Inventing or redefining a metric without approval.
- Presenting a product decision as if it were agreed.
- Over-extending a rule, or adding a mechanism unilaterally to satisfy a tool.
- Doing real logic in the consumption/frontend layer instead of upstream.
- Spot-fixing a data bug one layer at a time without the end-to-end picture; narrowing
  coverage to make a test pass; asserting before measuring.
