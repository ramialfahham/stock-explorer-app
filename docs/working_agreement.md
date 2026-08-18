# Working Agreement — UX PR gate

> **Agent process moved.** The general working agreement (how any AI agent operates here:
> the Explore → Plan → Confirm → Implement → Verify protocol, task contracts, review cycle,
> branch rules, decision rights, escalation) now lives in
> [`.claude/working-agreement.md`](../.claude/working-agreement.md) — adopted from the
> [`dbt-agent-kit`](https://github.com/ramialfahham/dbt-agent-kit) plugin. Read that first.
>
> This file keeps only the **project-specific UX PR gate** below, which is not part of the
> generic agreement.

---

## UX PR gate (user-facing frontend)

Applies to Streamlit layout, copy, and interaction changes — not dbt-only or ops-only PRs.

Before opening a UX PR:

1. **north_star check** — tab behavior matches [`north_star.md`](north_star.md) (especially Saved = learning list + single focus).
2. **Component specs** — layout changes must match [`docs/ui/`](ui/) (design tokens, Saved list, Discover header, card metric cell).
3. **One primary job** — PR description includes one sentence: what the user can do after merge.
4. **Mobile wireframe** — ASCII or sketch in the PR body for new layout patterns (required for Saved, Discover chrome, or card structure changes).
5. **480px smoke** — no horizontal scroll on Saved; Save still reachable on Discover; three hero metric values visible without scroll.

Audit or premortem tasks that change UI must pass this gate — not ship as silent engineering deliverables.
