# Review

diff_sha256: 8ff5783c659a2e69a7866dac4d8de834d4b7da55dc4a5d0409f0b979cc277af5
rounds: 1

README product-first. Round 1 on the cumulative diff (tree 813ee53). Routing requires
scope-auditor only (README.md matches no routed path).

Coordinator evidence: a line-multiset diff of README.md against main shows the only lines
that are not verbatim moves are the five approved changes (the diagram node, the new design
decision, the "For contributors" heading and the three demoted headings, the `validate`
line). Em-dash and context budget checks pass.

## scope-auditor

VERDICT: PASS
reviewed_tree: 813ee53ca58554b88bbbeabd3d53645f090442d1
risks_checked:
- The archive node's placement and "before the transform" match `.gitlab-ci.yml` (archive
  after ingestion, before dbt).
- Moved "Getting started" text is byte-identical to the original.
