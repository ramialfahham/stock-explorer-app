export const meta = {
  name: 'quality-baseline-audit',
  description: 'Read-only audit against docs/quality_criteria.json: an auditor per area, a skeptic per area with findings (14 agents at most)',
  whenToUse: 'Re-run the quality-baseline audit behind milestone "3 · Professional baseline". Then run scripts/verify_quality_audit.py on the workflow output JSON.',
  phases: [
    { title: 'Audit', detail: 'one auditor per area, findings must cite rule, file, line and verbatim evidence' },
    { title: 'Verify', detail: 'one skeptic per area tries to refute every finding' },
  ],
}

const CRITERIA = (args && args.criteria_path) || 'docs/quality_criteria.json'
const AREAS = (args && args.areas) || ['ingestion', 'dbt', 'export', 'frontend', 'docs', 'hygiene', 'guardrails']

const KIND = { type: 'string', enum: ['defect', 'documented_decision', 'unenforced_standard', 'proposed_rule'] }

const FINDINGS = {
  type: 'object',
  properties: {
    findings: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          criterion_id: { type: 'string' },
          kind: KIND,
          file: { type: 'string', description: 'repo-relative path' },
          line: { type: 'integer' },
          evidence: { type: 'string', description: 'verbatim text copied from file at line (1-3 lines, exact characters)' },
          rule_source: { type: 'string', description: 'the written rule violated: file + section, or "none" for proposed_rule' },
          explanation: { type: 'string' },
          already_tracked: { type: 'string', description: 'open issue number like #40 that already covers it, else empty' },
          proposed_fix: { type: 'string' },
        },
        required: ['criterion_id', 'kind', 'file', 'line', 'evidence', 'rule_source', 'explanation', 'already_tracked', 'proposed_fix'],
      },
    },
    checked_clean: { type: 'array', items: { type: 'string' }, description: 'criterion ids you checked and found no violation for' },
    not_checked: { type: 'array', items: { type: 'string' }, description: 'criterion ids or parts you could not check, with the reason' },
  },
  required: ['findings', 'checked_clean', 'not_checked'],
}

const VERDICTS = {
  type: 'object',
  properties: {
    verdicts: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          index: { type: 'integer' },
          confirmed: { type: 'boolean' },
          kind: KIND,
          reason: { type: 'string' },
        },
        required: ['index', 'confirmed', 'kind', 'reason'],
      },
    },
  },
  required: ['verdicts'],
}

const READ_ONLY = 'You are STRICTLY READ-ONLY, working in this repository\'s root. Use Read, Grep and Glob. You may run read-only shell commands (git grep, git ls-files, git log, glab issue list, python one-liners that only read and print). Never edit, write, create, delete, stage, commit, or run tests or scripts that write files.'

const auditPrompt = key => `${READ_ONLY}

You audit ONE area of this repository against FIXED, owner-approved criteria. Read ${CRITERIA} and use ONLY the area whose key is "${key}" (its "row", "paths" and "criteria").

Rules that keep this audit honest and repeatable:
- Report a finding ONLY against one of this area's criterion ids. Do not invent criteria.
- Each finding must cite: the criterion id; the written rule it violates (rule_source: the file and section named in the criterion's "source", which you must open and confirm says what you claim); the repo-relative file and 1-based line; and "evidence" copied VERBATIM from that file at that line (exact characters, 1-3 lines). No paraphrase in evidence.
- kind: "defect" = the code or doc violates the written rule; "documented_decision" = the repo documents this as a deliberate choice (cite where) but it is worth revisiting against the criterion; "unenforced_standard" = the rule exists and currently holds or mostly holds, but nothing (test, CI check, hook) enforces it; "proposed_rule" = it looks unprofessional but NO written rule covers it (rule_source "none") -- the owner decides, it is not a violation.
- Run \`glab issue list --per-page 100\` once. If an open issue already covers a finding, set already_tracked to its number (e.g. "#40").
- Prefer fewer, solid findings over many weak ones. Do not report style preferences. Do not report something you have not opened and read.
- List every criterion id you checked and found clean in checked_clean, and anything you could not check (with reason) in not_checked.`

const verifyPrompt = (key, findings) => `${READ_ONLY}

You are a skeptic. Another agent audited the "${key}" area of this repository against the fixed criteria in ${CRITERIA} (area key "${key}"). Try to REFUTE each finding below. For each one:
1. Open the cited file at the cited line. If the evidence is not there verbatim (allow +-3 lines for a quote of 10 or more normalised characters; a shorter quote must be the whole cited line), it is refuted.
2. Open the cited rule_source. If the written rule does not actually say what the finding claims, it is refuted (unless kind is proposed_rule).
3. Look for what would make it not a defect: a test that covers it, a documented deliberate decision (then the kind should be documented_decision), code elsewhere that handles it, or a misreading.
4. Re-classify kind if the auditor chose wrongly.
Default to confirmed=false if you are uncertain. Give a one-sentence reason citing file:line for every verdict.

Findings (index: JSON):
${findings.map((f, i) => `${i}: ${JSON.stringify(f)}`).join('\n')}`

const results = await pipeline(
  AREAS,
  key => agent(auditPrompt(key), { label: `audit:${key}`, phase: 'Audit', schema: FINDINGS }),
  async (audit, key) => {
    if (!audit) return { key, audit: null, verdicts: [] }
    if (!audit.findings.length) return { key, audit, verdicts: [] }
    const v = await agent(verifyPrompt(key, audit.findings), { label: `verify:${key}`, phase: 'Verify', schema: VERDICTS })
    return { key, audit, verdicts: v ? v.verdicts : null }
  },
)

const out = results.filter(Boolean).map(r => {
  if (!r.audit) return { area: r.key, error: 'auditor returned nothing' }
  const byIndex = new Map((r.verdicts || []).map(v => [v.index, v]))
  return {
    area: r.key,
    checked_clean: r.audit.checked_clean,
    not_checked: r.audit.not_checked,
    verify_missing: r.verdicts === null,
    findings: r.audit.findings.map((f, i) => {
      const v = byIndex.get(i)
      return { ...f, confirmed: v ? v.confirmed : null, verified_kind: v ? v.kind : null, verify_reason: v ? v.reason : 'no verdict' }
    }),
  }
})
const total = out.reduce((n, a) => n + (a.findings ? a.findings.length : 0), 0)
const kept = out.reduce((n, a) => n + (a.findings ? a.findings.filter(f => f.confirmed).length : 0), 0)
log(`${total} findings raised, ${kept} survived the skeptic`)
return out
