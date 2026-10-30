# Preserve byte-comparison inputs

Three existing analysis commands could replace their own consumed inputs with a
JSON report while returning success: `pump_compare_function_bytes.py`,
`pump_exact_body_inventory.py`, and `pump_quote_control_function_match.py`.
The shared report-admission helper now rejects output paths resolving to a
consumed input, including symlink and existing hardlink aliases, before analysis
or publication. The protected set includes the candidate, captured original,
selected window inventory where used, executed source helpers, and objdump.
Distinct report destinations retain their existing replacement behavior.

The reproduction uses the retained unstripped candidate at
`reconstruction/pump-main/lanes/v3-sell-payment-layout/candidate.so.gz`, whose
archive and build-record hashes are checked against that packet's manifest.
The decompressed ELF matches the recorded `unstripped_sha256`:
`969811b0e0f673b693695ea651008cacd93eafa5a663dd8bec0e61d3b22d09a9`.
Original Pump bytes and the actual 1,035-window inventory are also copied from
the repository. Every negative case changes only disposable copies, including
a copy of the real objdump executable. No compiler or symbol-reader response is
fabricated, and no repository capture is overwritten.

On Linux Python 3.12.14 and LLVM 14.0.0, the before version exits successfully
and changes input bytes in all 25 alias cases. The fixed version rejects those
cases and leaves their bytes unchanged. Five tests also check valid reports,
repeat publication, selection of an archived window inventory, and a real executable
selected through PATH. Previously `--objdump llvm-objdump` ran the tool but failed
when hashing its unresolved name. The inventory now resolves it once for execution
and provenance; the bare-name report equals the absolute-path report. The valid
exact-body report contains all 1,035 windows, including 188 raw-equal windows
for this retained candidate.

Normal before/after runs used the same LLVM executable and candidate. The
single-window and quote-control reports are byte-identical. All exact-body
inventory analysis fields and all 1,035 window records are unchanged; only its
`script_sha256` and `helper_sha256` provenance fields change as expected.
`results.json` retains the source/tool/input hashes and individual outcomes.

Run from the repository root with a real LLVM objdump installed:

```sh
python -B reconstruction/tooling/byte-comparison-input-preservation/test_verify.py --objdump /usr/bin/llvm-objdump
python -B scripts/test_pump_quote_control_function_match.py
python -B scripts/test_pump_window_inventory.py
python -B scripts/test_pump_compare_window_selection.py
python -B scripts/test_tooling.py
python -B scripts/verify_evidence.py
```

To reproduce the before failures, add `--source-revision BASE` using the base
revision in `proposed-asset-transition.json`. The test reads those three script
blobs without altering the checkout. Alternatively, export the three scripts
into a separate directory and pass `--script-directory PATH`. `--report PATH`
records individual outcomes in a new JSON file.

This is input preservation for the three local analysis commands, not a fresh
build, scoring improvement, runtime-equivalence claim, or transaction across
concurrent filesystem changes. Historical evidence and source bindings are not
rewritten; the proposed asset transition is for maintainer review.
