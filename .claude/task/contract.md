# Task contract
> DISPOSABLE. **Owns:** THIS task's objective, `scope_paths`, reserved decisions and
> `done_when`.
> **Never:** anything that outlives the task. Overwritten by the next one.

objective: Give every context file a stated owner, and move the rules that gate every commit out
  of the files designed to be thrown away.

  Measured, not assumed. The repo-wide "no em/en-dash on any line added" rule exists in exactly
  two places: `.claude/active_work.md` and `.claude/task/review.md`. The handover is trimmed
  every pass to stay under a 32,000-byte cap; the task contract and review are overwritten by the
  next task. A rule that blocks every commit lives only in files whose job is to be discarded,
  which is why it keeps being re-learned from a memory file instead of read from the repo.
  (`docs/data_contract.md:605` also bans em-dashes, but in AI-generated card prose. Different
  rule, not this one.)

  The same shape, measured across the repo: decision rights are asserted in six files, "what
  fails CI" in five with no owner, and metric definitions in three besides the `metric_catalogue`
  seed that `docs/metric_layer.md` declares the single source of truth. Two files are named
  "working agreement", differing only by hyphen versus underscore.

  The rule that explains all of it: files split by LIFETIME, and durable content has been living
  in disposable files.

scope_paths:
  - CLAUDE.md
  - .claude/working-agreement.md
  - .claude/active_work.md
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/skills/onboard-market/SKILL.md
  - docs/engineering_standards.md
  - docs/data_contract.md
  - docs/layering.md
  - docs/metric_layer.md
  - docs/north_star.md
  - docs/project_context.md
  - docs/development_workflow.md
  - docs/operations_guide.md
  - docs/working_agreement.md

decisions_reserved:
  - THE CONVENTION ITSELF is a change to how this repo works, so §6. Asked and answered: the
    owner described the problem (files with no defined purpose, contradictory entries, bloat,
    losing track of which source has authority) and approved this order of work. The convention
    adopted: DURABLE files hold rules, contracts and definitions; DISPOSABLE files hold state.
    Nothing permanent may live in a disposable file, and no state may live in a durable file.
  - The rule against dated decisions in code lands here; the existing code sites are swept in a
    separate change. Both that sweep and the working-agreement rename are recorded in
    `.claude/active_work.md`, not in this file, because this file is overwritten by the next task.

done_when:
  - Every context file in `scope_paths` opens with a statement of what it owns and what it must
    never contain, and that statement is TRUE of the file as staged. `SKILL.md` is in scope only
    to repair a pointer this diff's own deletion broke; it is a procedure, not a context file,
    and takes no header. `CLAUDE.md` is the exception it
    declares itself to be: it is injected every session, so it restates the one hard rule a
    session must not miss and says the linked doc wins on conflict.
  - The repo-wide em/en-dash prohibition and the no-date-stamping rule move to
    `docs/engineering_standards.md` §1.2 and §1.3. "Changelogs live in one place" does NOT move
    there: `.claude/working-agreement.md` §2 already owned it, so §1.3 points at that instead of
    creating a second durable copy.
  - `.claude/active_work.md`'s standing decisions that merely restate a durable doc are deleted,
    not copied. Verified per entry before removal: seven of ten checked were already stated in
    `docs/data_contract.md`, `metric_catalogue.csv` or `docs/ui/`.
  - `.claude/active_work.md` gets materially smaller and holds only state: what is in flight,
    what is open, what a future session must act on.
  - No rule is deleted without a durable home. Each removal names where it now lives.

impact_map: Documentation only. No executable line, no schema, no CI. The risk is deletion:
  removing a handover entry whose durable twin says something subtly narrower. Each removal is
  checked against the twin's exact wording first, and the reviewers are asked to verify the pair
  rather than the removal alone.
