# Analyzer root binding

At `1cacecfbf9a58b698f99d5e11d6723a254588b81`, `python3 -B scripts/test_tooling.py` fails with three errors
across 40 tests. The existing interface-inventory test replaces `analyze.ROOT`
and copies the retained Mayhem capture into its temporary root. However,
`program_names(root=ROOT)` retains the import-time repository root and selects
Pump as well. `analyze()` then tries to open a missing Pump ELF under the
temporary root. Both locale subtests fail, followed by their missing-output
assertion.

Resolve an omitted root at call time. Explicit roots, archived selector
precedence, capture ordering, ELF parsing, and missing selected-file errors
keep their existing behavior. The real Mayhem fixture and all captures remain
byte-identical. Two regression controls cover explicit-root precedence and
missing selected binaries; the existing fixture provides the real successful
ELF/IDL analysis under both encoding defaults.

The same required commands at source commit `41ffcc97f8ae009c151abf3d1cc27f5d0672738b` pass:

```sh
python3 -B scripts/test_tooling.py
python3 -B scripts/verify_evidence.py
```

The results are 42 passing tests and nine verified captures. `RESULTS.json`
binds 65 declared maintained source/capture/metadata inputs before/after,
with only the production function and its test file changed. The list is a
superset, not a syscall trace; three unused metadata files were materialized
after the run for this binding, as recorded in its limits. It also binds the
unchanged Mayhem fixture. Raw output is retained in four log files.
`MANIFEST.json` seals this packet. The later packet-only commit preserves the
exact two tested source blobs; it does not relabel the original command run.

An initial sparse-checkout run additionally lacked the tracked
`evidence/binary-analysis.json`. That setup failure is retained privately and
was corrected by materializing the exact base blob before the authoritative
before/after runs. No fixture or file validation was relaxed.

This fixes required on-chain verification tooling. It changes no program
source and makes no compiler, VM, byte-match or security claim. Nearby
PR #1673 sorts IDL iteration; #1842 binds parsed snapshots; #1731 specifies
packet encodings. Their changes are outside this function.
