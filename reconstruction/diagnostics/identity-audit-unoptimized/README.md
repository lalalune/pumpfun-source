# Reviewed identity audit entrypoint

This entrypoint admits the reviewed identity audit, analyzer and comparator
sources, then runs private copies of those admitted bytes in a fresh unoptimized
isolated Python interpreter. Later changes to the public script paths cannot
change the code executed by that child. The explicit repository argument still
selects the audit inputs.

```sh
python -B reconstruction/diagnostics/identity-audit-unoptimized/run.py --repo . --index selected-index.json --output work/identity-audit-new.json
python -B reconstruction/diagnostics/identity-audit-unoptimized/test_run.py
```

The maintained audit now rejects incorrect original/candidate hashes and refuses
to replace existing reports even when called directly with optimized Python.
This wrapper additionally checks the three reviewed source digests and isolates
the child from parent `-O`/`-OO` flags and inherited `PYTHONOPTIMIZE`. A reviewed
change to those source files requires updating `REVIEWED`; source hashes accept
LF and CRLF line endings. The earlier digest set and test expectations had become
stale and prevented this entrypoint from running against the maintained scripts.

Tests run actual CLI audits over retained Associated Token ELF bytes and explicit
checksum-bound control indexes. They check incorrect bindings, existing and late
reports, changed source rejection, and source replacement after admission. An
identical-capture control retains the no-source/no-compiler-identity qualifications;
missing current-status data remains explicitly reported. No contract is compiled
or executed, and no reconstructed candidate or runtime acceptance is claimed.

The child uses exclusive output creation, so an existing or late report is
preserved. This does not promise atomic publication of a completed report on a
write failure or freeze the input files before the maintained audit reads them.
