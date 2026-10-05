# Review

diff_sha256: e6c81c2eae942a8bcec0094adf9c606b89d551fa669af3f2047d354499f17550
rounds: 1

`.mailmap`. Round 1 on the cumulative diff (tree d48664f). Routing requires scope-auditor only
(`.mailmap` matches no routed path).

Coordinator evidence: with the file in place, `git shortlog -sne --all` shows one author,
979 commits (618 + 235 + 104 + 22); `git check-mailmap` maps all four identities to
`Rami Al-Fahham <rami.fahham@googlemail.com>`. Em-dash and context budget checks pass.

## scope-auditor

VERDICT: PASS
reviewed_tree: d48664fc8f53a0eecd70f8f0cda2b66d67fd5637
risks_checked:
- Completeness: two email-matched lines cover every non-canonical address, including both
  names used with the GitHub noreply address; shortlog confirms one author.
- Format: canonical identity left, commit-time email right; file ends with a newline.
