# Check the generated packet directory

The generated verifiers in `deep_disassembly.py`, `deep_section_analysis.py`
and `bytecode_signatures.py` validate manifest membership and each listed file's
hash, but did not compare the actual directory entries with that membership.
A stale or unlisted analysis file added after generation was silently ignored,
and verification still printed `All checks passed.` with exit status zero.
The generators already require exactly their generated entry set before writing;
this repair applies that same contract when the retained packet is verified.

Base revision: `6ac6f9b6789b0dddcbf03989f5b8511e732bdb3e`.
The proposed source hashes are recorded in `proposed-asset-transition.json`.
This proposal changes three existing script assets, not the root script set.
No historical packet, archived verifier, prior proposal or frozen seal is edited.

Each new verifier compares the actual entry names with its existing
`EXPECTED_FILES` plus `manifest.json`, before opening the manifest. Extra regular
files, directories and dangling symlinks fail without deletion. Manifest-key,
missing-file and per-file hash checks remain enforced.

## Actual capture workflow

Run from the repository root with the pinned Python requirements installed:

```sh
python -B tests/test_generated_packet_census.py -v
python -B scripts/test_deep_disassembly_publication.py
python -B scripts/test_deep_disassembly_syscall_usage.py
python -B scripts/test_deep_section_analysis_publication.py
python -B scripts/test_bytecode_signatures.py
python -B scripts/test_bytecode_signatures_publication.py
python -B scripts/test_bytecode_signatures_atomic_publication.py
python -B research/tooling-disassembly-reproducibility-20261030/test_verify.py
python -B reconstruction/tooling/deep-analysis-output-links/test_verify.py
python -E -B -X utf8 scripts/verify_evidence.py
python -E -B -X utf8 scripts/test_tooling.py
```

The new test invokes all three actual generator CLIs and their generated verifier
scripts. Deep disassembly and section analysis read the captured Mayhem image;
bytecode signatures reads the captured Pump, PumpSwap and Mayhem images.
The standalone Mayhem reproduction contains 441 windows and uses capture SHA-256
`a87fa9f866272514e6acb852b668c4a08aeb173d56c883039991d114d1199bdb`.
It adds an `unlisted-analysis.json` file only after a clean packet verifies.
All three base verifiers still exit zero; the corrected verifiers reject it.

On macOS27.0.1 arm64 / Python3.12.13, the same six-method test has nine failing
subtests at base (extra file, directory and link across three generators), then
all six methods pass after the repair. The 37 related methods, one real
reproducibility method, 214 required tooling methods and nine capture checks
pass. The output-link suite runs four methods: three pass and its existing
Windows-junction method is skipped on this host. `git diff --check` passes.

A separate real base/fixed regeneration at each identical output path confirms
that only `verify.py` and `manifest.json` change. All 27 other files across the
three packets remain byte-identical. `results.json` retains the before/after
hashes. This is analysis packet validation, not compilation, runtime replay,
reconstruction-score progress, or protection against concurrent filesystem
mutation. No Linux or Windows execution is claimed.
