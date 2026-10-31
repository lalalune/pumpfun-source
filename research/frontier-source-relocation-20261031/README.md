# Replay source relocation

The macOS frontier replay stages the retained workspace under a fresh `.candidate-*` directory. Its native build receipt still names `work/pump-macos-qualification/candidate/source`, the path used by the original builder. At base `720311c88e547c3a2d5ada174429a18e53c4fd83`, replay hashes those original names before validation, producing `FileNotFoundError` in a clean checkout. Rebasing that check alone is insufficient: the actual parallel validator requires the current staged source manifest.

The correction verifies each original digest against its restored workspace file, preserves repository-level inputs at their original paths, and writes a separate execution-time `replay-build-comparison.json`. The original `build-comparison.json` remains byte-for-byte intact. The derived receipt records its origin hash and both workspace prefixes. The parallel validator authenticates that origin, accepts only the declared prefix relocation, refuses changes to other build fields, and protects the origin receipt alongside its other runtime inputs.

Run the retained reproduction from a checkout using its installed requirements:

```sh
python -B research/frontier-source-relocation-20261031/probe.py "$PWD"
python -B scripts/test_replay_macos_frontier.py
```

The probe uses real tar extraction and the real `validate_build_sources` implementation on a local four-file Cargo workspace. It deliberately stops before VM execution. Before: `FileNotFoundError`, `validator_admitted: false`. After: `validator_admitted: true`, four manifest entries, and `original_record_preserved: true`. Exact outputs are retained in `before.json` and `after.json`.

Eight workflow tests passed, covering actual validator admission, changed and added Rust inputs, repository config binding, original receipt mutation, derived build-field mutation, absolute/parent-traversing binding paths, failure/retry and publication. The packet-publication tests supply synthetic VM suite results; those results are not runtime evidence. Eight parallel-validator tests, two optimization guards, 250 tooling tests, and nine evidence captures passed.

This is a staging and provenance integration fix. It does not rebuild a program or claim the full corpus passed. Published receipts continue to record execution-time staging paths as historical provenance; the original native receipt and original source names remain available separately.
