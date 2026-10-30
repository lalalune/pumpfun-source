# Admit the complete analysis input set before publishing reports

`scripts/analyze.py` generates `binary-analysis.json` and
`interface-inventory.json` from the retained on-chain ELF and IDL evidence.
Previously it replaced the binary report before reading the interface IDLs.
A malformed JSON document or an IDL missing `instructions` then aborted the run,
leaving a newly replaced binary report beside the previous interface report.
The same failed first run published a binary report without its counterpart.

The proposed script asset transition moves all input parsing and both JSON
serializations before either write. The valid workflow and report format are
unchanged. No original capture, stored report, historical script manifest or
checkpoint is re-sealed. `transition.json` binds the base and proposed script.
No root script is added, renamed or removed.

## Repeatable evidence

From the repository root:

```
python -I -B -X utf8 tests/test_analyze_input_admission.py
python -I -O -B -X utf8 tests/test_analyze_input_admission.py
python -E -B -X utf8 scripts/verify_evidence.py
python -E -B -X utf8 scripts/test_tooling.py
```

The regression runs the actual analyzer CLI in isolated filesystem trees with
the complete retained Mayhem ELF and original upstream IDLs. It copies the
checked-in prior reports and compares their exact bytes after each rejected run.
The base produces three failing cases (invalid JSON, missing IDL structure and
first-run publication) while the valid retained-evidence case passes. With the
transition, all three test methods pass, including the two rejection subcases,
in ordinary and optimized interpreters. The positive run verifies the meaningful
ELF hash, allocation length, program inventory and declared IDL counts/addresses.

The Mayhem input is 777,408 bytes, SHA-256
`a87fa9f866272514e6acb852b668c4a08aeb173d56c883039991d114d1199bdb`.
The required saved-evidence verifier passes all nine captures. The full tooling
suite was attempted with the exact pinned packages on Windows; it fails before
test execution because the official solders 0.27.1 wheel lacks native
`FeatureSet`, required by `solders.litesvm`. No runtime substitute was used.

## Limits

This preserves report pairs when input parsing, analysis or serialization fails.
It does not make two filesystem writes transactional: a write error or process
interruption during publication may still leave partial output. It does not add
new ELF/IDL admission rules, change capture bytes, prove a fresh build, execute a
VM, increase byte-match counts or establish security acceptance.
