# Retained research manifest formats

The audit runner only looked for `manifest.json` and interpreted its JSON as a
flat path-to-SHA-256 map. Current main also retains twelve packets using
`MANIFEST.json` with a `files` array of path/hash records and optional byte
counts. On a case-sensitive checkout those manifests are not discovered. On
Windows the lowercase lookup finds the uppercase file, but treats `files` as
a member name and reports `missing: files` without hashing a packet member.

A concrete reproduction uses the unchanged
`amm-multi-hop-fee-table-split-liquidity-chains-20261029` packet: all 28 members
(721,540 bytes) match their committed hashes and lengths, but the old checker
reports `fail`, `files_checked: 0`, `files_expected: 1`, `missing: files`.

## Supported formats and scope

The checker now recognizes exact `manifest.json` and `MANIFEST.json` directory
entries, rejects ambiguous presence of both, and accepts the two retained
formats: a flat hash map or a `files` list with `path`, `sha256` and optional
`bytes`. The three mode/tf chain packets omit byte counts, so omission is valid.
When present, byte counts must be nonnegative integers and must match the file.
All members require a valid lowercase SHA-256 and matching file bytes.
Malformed records, duplicate paths, missing members and directory substitutions
do not produce a passing manifest check. Unknown record fields are rejected.

The main audit's discovery and manifest counts use the same filename selector.
The complete retained census is twelve record manifests with 297 members plus
four flat manifests with seven members each. All sixteen are exercised without
executing their producers or standalone verifiers. Historical packet bytes,
manifest contents, captures and expected hashes remain unchanged.

This is a format compatibility correction, not a new manifest authority or
security boundary. Existing whole-audit status aggregation is unchanged; a
successful standalone verifier can still override a failed manifest under the
old OR rule. Pending PR #1362 addresses that separate behavior. PR #1382 covers
output discovery/publication and #1709 covers verifier invocation arguments.
This change does not implement those corrections.

## Reproduction

Baseline: `094a06f18df738d41e77070c1a009e135671ac1a`.
Run from the repository root with Python 3.12 and preserved Git checkout bytes:

```sh
python -B research/tooling-revalidation-manifests-20261030/test_verify.py
python -B scripts/test_tooling.py
python -B scripts/verify_evidence.py
```

The six focused tests check all 325 retained members, both formats, exact name
selection and ambiguity, malformed records, and copied real-packet mutations
(one changed byte, wrong declared size, missing member, and directory replacement).
A CLI integration control confirms an uppercase record manifest is discovered
and counted in the generated report. Before the correction all twelve actual
record manifests fail on Windows; afterward all sixteen retained manifest checks
pass. Ten existing tooling tests and all nine capture checks also pass.

No full research audit or contract execution is claimed. Some standalone packet
verifiers have additional environment dependencies or historical source drift;
passing a manifest check proves only consistency with that manifest.
