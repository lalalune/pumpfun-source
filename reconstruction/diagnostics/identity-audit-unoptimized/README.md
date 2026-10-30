# Optimization-safe identity audit entrypoint

The retained identity audit enforces expected snapshot hashes and output retention
using `assert`. Running it with `python -O` accepts an index with an incorrect
original/candidate hash and can overwrite an existing successful audit receipt.

```
python -B reconstruction/diagnostics/identity-audit-unoptimized/run.py --repo . --index selected-index.json --output work/identity-audit-new.json
python -B reconstruction/diagnostics/identity-audit-unoptimized/test_run.py
```

This explicit successor admits the reviewed audit/analyzer/comparator source
hashes, refuses an existing output and delegates the unchanged audit to a fresh
unoptimized isolated interpreter. Both parent `-O`/`-OO` flags and inherited
`PYTHONOPTIMIZE` are prevented from disabling the retained checks. The old root
helpers and historical artifacts remain unchanged.

Tests run the actual old and guarded CLIs over authentic retained Associated
Token ELF bytes and explicit checksum-bound control indexes. The old optimized
CLI accepts wrong hashes and replaces a prior real report; the guarded entrypoint
rejects both, while a valid optimized invocation still produces a correctly bound
report. Identical-capture controls explicitly retain the no-source/no-compiler-
identity qualifications. No program is compiled or executed; this is not a newly
built candidate, VM result, source-equivalence or security acceptance claim.

Other archived audit limitations remain, including the separate missing-current-
status and input-path changes tracked in #1475 and #1642. A source transition needs
reviewed digest updates. Output retention here covers already-existing outputs,
not interprocess atomic publication. Use this explicit successor when auditing;
direct optimized invocation of the archived root helper retains its old behavior.
