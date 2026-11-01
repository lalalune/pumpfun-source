# Preserve an explicitly empty symbol regex

`win.py show` documents `--sym REGEX`, and its parser accepts an empty regex.
On the retained 1,090-function Pump artifact, `--sym ''` nevertheless takes the
absent-filter heuristic path and reports only three candidates. The equivalent
valid regex `--sym '(?:)'` reports all 1,090. The `win.py sym` subcommand and
`target_metric.py --sym` already treat these patterns identically.

The existing condition tests string truthiness. Checking whether the option is
present instead selects the existing regex branch for an explicitly empty
pattern. No ranking, scoring, matching, disassembly or regex implementation changes.
For this witness, the selected top body is identical before and after; the defect
is the silently omitted requested candidate scope.

This retains the CLI validation scope accepted in
[#2142](https://github.com/lalalune/pumpfun-source/pull/2142) by **mapmapdown**
and symbol-listing semantics from
[#3323](https://github.com/lalalune/pumpfun-source/pull/3323) by
**dbstkddl8-create**. Neither establishes an empty-pattern exception. The existing
[`BATCH_METRICS.md`](../../reconstruction/harness/BATCH_METRICS.md) also documents
that explicit `--sym` selection reports every matching symbol.

| Actual command case | Before candidate rows | After candidate rows |
| --- | ---: | ---: |
| `show` without `--sym` | 3 | 3 |
| `show --sym ''` | 3 | 1,090 |
| `show --sym '(?:)'` | 1,090 | 1,090 |
| `show --sym '^custom_panic$'` | 1 | 1 |
| `sym ''` / `sym '(?:)'` | 1,090 each | 1,090 each |
| `target_metric --sym ''` / `--sym '(?:)'` | 1,090 each | 1,090 each |

No-match `show` still exits 1, and invalid-regex `show` still exits 2. Across the
ten actual CLI cases per revision, only `show --sym ''` changes its output.
Its complete output after the correction equals the equivalent-regex output.
All nine controls have byte-identical stdout/stderr and unchanged exit codes.

## Replay

Use the existing official v1.44 `llvm-objdump`; this probe does not install tools.

```sh
python -B research/window-empty-symbol-regex-20261101/probe.py --repo . \
  --objdump /path/to/platform-tools/llvm/bin/llvm-objdump \
  --revision 60a42309a4908577f0a386513eeaee6cd6f84f42 --expect base --output /tmp/regex-before.json
python -B research/window-empty-symbol-regex-20261101/probe.py --repo . \
  --objdump /path/to/platform-tools/llvm/bin/llvm-objdump \
  --expect fixed --output /tmp/regex-after.json
python -B tests/test_window_empty_symbol_regex.py
python -B reconstruction/harness/test_window_cli.py
python -B reconstruction/harness/test_window_symbol_admission.py
python -B reconstruction/harness/test_batch_target_metric.py
python -B reconstruction/harness/test_candidate_limit.py
python -B reconstruction/harness/test_pair_candidates_limit.py
python -B scripts/verify_evidence.py
```

The unchanged retained input is
`research/pump-multihop-token-quote-20261029/build/parent/symbols.so.gz`, with
decompressed SHA-256
`e1c9bdc3b248d41ebd73c1f8d0d2756edf95eafa178b8aed4a8ae0715649705a`.
The probe stages exact helpers, the real Pump capture and selected-window
inventory in an owned temporary directory. It runs the complete CLI and actual
official objdump, preserving all source/input/tool bytes. Exact hashes and results
are recorded in [`results.json`](results.json).

Measured on macOS arm64 with CPython 3.12.13 and official SDK v1.44 objdump.
All 25 affected static test methods and nine capture checks pass. The three new
tests run through existing `tests/` CI discovery. They use the genuine retained
ELF and real selection/ranking/diff logic, omitting only external assembly-text
rendering so the unit test does not need an SDK. The separate public proof uses
actual rendering. No compiler, program image, native model or VM is executed by
this proof; no runtime-equivalence or score-improvement claim is made.
