# Fees aggregate output preservation

The aggregate pinned the candidate, then wrote its report directly to the caller's
output path. On base `60803449039c31d9eae026ee62bdd3e0f30f5afa`, using a private copy
of the captured Fees ELF as both `--candidate` and `--output` completed all 18 real
LiteSVM suites (17,331 cases, zero mismatches, exit 0), then replaced that ELF with
JSON. `results.json` records the before/after hashes and controls.

The fix admits the original candidate path and suite inputs through the existing
`PumpReport` publisher before pinning or launching a suite. Publication uses that
same helper, so a failed staging write also preserves a prior complete report.
All Python source files under `scripts/` are protected because child-process
imports cannot be discovered from the parent process's loaded modules. Normal
JSON output replacement remains supported.

With pinned `requirements.txt` installed, reproduce only on a private copy:

```sh
tmp=$(mktemp -d)
cp evidence/original/pump_fees/deployed.so "$tmp/candidate.so"
python scripts/fees_validate_all.py --candidate "$tmp/candidate.so" --output "$tmp/candidate.so"
# Base: exit 0 and candidate becomes JSON. Fixed: alias error before execution.
python scripts/fees_validate_all.py --candidate evidence/original/pump_fees/deployed.so --output "$tmp/normal.json"
# Fixed normal control: 18 suites, 17,331 cases, zero mismatches.
```

The focused regression is `python -B tests/test_fees_aggregate_output.py -v`.
Its small child receipts isolate the real aggregate CLI's filesystem boundary;
they are not SBF behavior evidence. The separate manual run above uses the real
18-suite corpus. It also exercises direct/symlink/hardlink candidate aliases,
child input preservation, nested output/replacement, and a real POSIX file-size
limit that interrupts report publication. No repository capture was modified.

Required checks: `python -E -X utf8 scripts/test_tooling.py` (214 pass) and
`python -E -X utf8 scripts/verify_evidence.py` (nine captures verified). Optimized
Python guard tests (three) and aggregate pinned-image tests (two) also pass.
macOS arm64, Python 3.12.13, solders 0.27.1; no Linux/Windows, compiler, source
reconstruction, score gain or new program-equivalence claim.

The initial sparse checkout omitted `research/fees-query-inputs`; the first run
stopped before execution, without changing its private candidate. That tracked
input directory was hydrated before the successful baseline and fixed runs.

`proposed-asset-transition.json` records the maintained script's old/new hashes;
no immutable historical evidence pins are rewritten.
