# Preserve serial validation inputs

The serial `scripts/pump_validate_all.py` driver writes each retained suite
report after checking its input hashes. An output alias can therefore replace
the candidate immediately after a successful suite. The next suite fails, but
the input is already lost. The aggregate destination has the same problem.

PR #2506 fixed the parallel driver. This serial fix was prepared as an extension
to that branch, but #2506 merged before the extension reached its merged head.
This follow-up supplies the undelivered serial behavior. The original parallel
packet, its captured results and its proposed asset transition remain unchanged.

The serial driver now admits its aggregate and all 44 retained suite paths
before its first subprocess. It protects the candidate, captured original,
runner, diagnostic helper, selected suite scripts, and Rust/manifest inputs in
the source directory. Canonical paths, symlinks and existing hardlinks are
checked by a shared helper used by both serial and parallel drivers. Missing
historical paths remain protected by pathname without calling `samefile` on a
nonexistent file. A workspace whose parent is named `target` still protects its
own source inputs; only paths inside the source tree's `target` components are
excluded.

## Actual reproduction

Base revision: `43daa2043fb4a87838d715ab61467e4213d76d66`.
Use the public candidate from [run 41013070961](https://github.com/miracle2044/pumpfun-source/actions/runs/41013070961),
artifact `proof-41013070961-1`, built from source revision
`8d9c088750e6005304d919fe71192ccea74aa42c`.
Candidate SHA-256:
`f8e03b83699a723a85e1b1aa22eb857987a65a85c5e14958e7c00b1287d37f46`.
Setup and the unmodified compiler receipt are described in the preserved
`../parallel-input-preservation-20261030/README.md`.

In a disposable projection, hardlink the private candidate to
`work/alias-proof/serial-hardlink.json.gz.suites/volume.json.gz`, then run:

```sh
python -B scripts/pump_validate_all.py \
  --candidate work/captured-loader-build/candidate.so \
  --source-directory work/captured-loader-build/source/programs/pump \
  --output work/alias-proof/serial-hardlink.json.gz
```

With the unchanged production suite list, the first suite completed 66 real
LiteSVM volume cases, then overwrote the candidate with its gzip report. The
next suite failed with `invalid account data for instruction`. The patched
driver instead rejects the alias before launching any suite and preserves the
candidate hash. All destructive testing used private copies restored afterward.

A noncolliding patched serial invocation completed the same 66-case suite
before being deliberately stopped. This is a bounded control, **not a claim
that all 44 serial suites passed**. The shared guard was also checked against
the real retained 2,605-case parallel report and seven input alias cases during
the original extension's validation. The new CLI regression uses captured ELF
bytes and the unchanged serial entry point to check aggregate, first/last suite
hardlink, and source-file conflicts before execution.

Environment: Ubuntu 22.04, Python 3.12.14, solders 0.27.1. Run
`python scripts/verify_evidence.py`, `python scripts/test_tooling.py`,
`python scripts/test_pump_validate_parallel.py`, the original parallel packet's
tests, and `python reconstruction/tooling/serial-input-preservation-20261030/test_serial_admission.py`.
The new CLI test is included in the evidence CI job. `results.json` records the
bounded observations; `proposed-asset-transition.json` binds both changed tools.
No captured bytes, historical evidence, suite expectations or program source
were changed. This does not provide filesystem race protection or establish
whole-program equivalence.
