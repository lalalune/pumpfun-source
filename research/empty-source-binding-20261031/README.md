# Empty source-directory admission

Five Pump validation suites record the Rust and Cargo inputs they were compared
against under `source_sha256`, and the aggregate driver launches them all. None
of them checked that the directory held any such input. At base
`5889e795eba64e85e613b4409921323bfecec414`, running
`pump_validate_authority.py` with an empty `--source-directory` completed 59
real cases, exited 0 and published a report with `"source_sha256": {}` — a
differential receipt that binds no source bytes.

`results.json` records that run and the refusal that replaces it. Each of
`pump_validate_buy.py`, `pump_validate_quote.py`, `pump_validate_sell.py`,
`pump_validate_config_admin.py` and `pump_validate_authority.py` now rejects a
directory without a `.rs`, `Cargo.toml` or `Cargo.lock` input immediately after
argument parsing, before any case runs:

```
no Rust/Cargo inputs under <directory>
```

The aggregate `pump_validate_all.py` applies the same check to its `source_paths`
list before `protect_inputs` and before the first suite is launched, so an empty
directory cannot produce a 44-suite report at all. `pump_validate_parallel.py`
already rejects an empty binding through `validate_build_sources`; the serial
aggregate had no equivalent guard.

`tests/test_empty_source_binding.py` runs each suite's real CLI against an empty
directory and drives `pump_validate_all.main()` with `subprocess.run` patched to
record and refuse any launch. All six cases fail on the base scripts (the suites
exit 0 having run their corpora; the aggregate launches a suite) and pass in
0.3s on the proposed scripts.

Required checks on the proposed tree: `python3 -E -X utf8 scripts/test_tooling.py`
(217 pass) and `python3 -E -X utf8 scripts/verify_evidence.py` (nine captures
verified). macOS arm64, Python 3.14.3. The default `programs/pump` directory,
case corpora, comparison fields and captured ELFs are unchanged; no
program-equivalence claim is made.

## Review qualification

The reviewed implementation enumerates each suite's Rust/Cargo inputs once at
admission, then hashes that same path list for the report. Removing an admitted
file during execution therefore fails instead of producing an empty binding.
The `target` exclusion is relative to the source directory; a source tree under
an ancestor named `target` remains usable. Configuration and aggregate admission
run before candidate pinning or report-directory creation.

The replacement regression tests invoke all six real entrypoints for missing,
empty, non-source and generated-only inputs. They execute all five unchanged
corpora against the captured Pump control (334/130/301/351/59 cases), check source
output aliases, and remove admitted files after real VM execution begins. These
presence/hash checks do not prove that the supplied source produced the ELF.
