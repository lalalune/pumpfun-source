# Forward the actual producer receipt after ELF snapshotting

At base `1043a51e8798c5974a84ecaed5c85e9d6938cfce`, the serial Pump
aggregate pins its candidate in a private temporary directory, but its
build-bound two-curve child discovers `build-comparison.json` beside that
snapshot. The genuine producer files remain beside the caller's selected
ELF, so the child fails reading the nonexistent temporary sidecar.
The parallel aggregate already forwards the producer receipt explicitly.

Resolve the selected candidate's original path before pinning; discover the
actual receipt there or accept `--build-report`. Keep both the real report
and sibling attempt file in protected inputs, hash and recheck them during
execution, and forward the receipt only to the build-bound child. Retain
their hashes in the final aggregate report. No invented receipt is copied
beside the snapshot, and existing child source/ELF admission stays intact.

The command helper factors the existing dispatch statements and adds one
suite-specific option. Other suite flags/cases, VM execution, signatures and
program source are unchanged. Supplemental publication-unit fixtures are
explicitly unit-only JSON inputs, not producer evidence.

## Genuine compiler and VM proof

Use Python 3.12 and pinned requirements on Linux x86_64:

```sh
python -B research/pump-serial-build-receipt/reproduce.py
python -B scripts/test_pump_validate_all_retention.py
python -B scripts/verify_evidence.py
python -B scripts/test_tooling.py
```

The same proof authenticates the official unmodified Linux v1.44 SDK with
the already-retained native SDK helper, freshly builds current Pump source,
and retains actual compiler diagnostics, producer/attempt records and ELFs.
It executes the baseline driver's actual command-construction statements
or the fixed production helper, then launches the unchanged 20-case LiteSVM
child. Before it fails finding the missing temporary sidecar. After it must
retain 20 matching pairs and 40 normally verified outer signatures. A
different actual captured ELF with the genuine receipt must be rejected.

This is a bounded actual dispatch/20-case proof, not a claim that all 44
historical suites pass. `SERIAL_FULL_CORPUS=1` is an explicit additional
full-corpus execution; it is not enabled by default or implied by the
bounded result. Genuine Linux SDK execution is not macOS qualification.
The existing child requires the producer path under the repository root;
the proof builds under `work/serial-current-build`. External-receipt path
support is outside this patch.

Missing producer records now fail before other suites consume runtime;
the complete serial corpus already needs them for its two-curve child.
This fixes receipt handoff in reconstruction tooling, with no new handler
coverage, whole-byte identity or security claim. Historical receipts remain
unchanged; the proposed asset transition lists only modified current scripts.
