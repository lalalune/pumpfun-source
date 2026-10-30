# Repository arguments for retained packet verification

The research audit runner starts each `verify.py` with its working directory
set to the packet. Four retained tooling verifiers instead document an explicit
`--repo` argument, default it to `.`, and require that path to be the repository
root. The runner omitted that argument, so these scripts stopped at their root
assertion before checking evidence. For example, the unchanged token-detector
verifier passes from the repository root but `revalidate_all.run_verify(packet)`
reports a failure when it runs the same file from its packet directory.

The runner now supplies the absolute repository path to exactly these documented
interfaces:

- `research/tooling-legacy-capture-metadata-20261029/verify.py`
- `research/tooling-roadmap-call-classification-20261029/verify.py`
- `research/tooling-source-manifest-symlinks-20261029/verify.py`
- `research/tooling-token-program-constant-detector-20261029/verify.py`

Each verifier declares `parser.add_argument('--repo', type=Path, default='.')`.
Their READMEs document invocation from the repository root (three explicitly
show `--repo .`). This is a reviewed invocation registry, not an attempt to infer
arbitrary command-line interfaces from source or by executing `--help`.
A packet must resolve to the registered path within this repository. A similarly
named external or nested directory does not receive the extra arguments.

All verifiers retain their packet working directory. This preserves existing
packet-relative file access and keeps unregistered commands unchanged. Child
failures and return codes remain failures. No archived verifier, manifest,
input hash, capture or packet is modified.

## Reproduction and checks

Baseline: `094a06f18df738d41e77070c1a009e135671ac1a`.
From the repository root on Python 3.12:

```sh
python -B research/tooling-revalidation-invocation-20261030/test_verify.py
python -B scripts/test_tooling.py
python -B scripts/verify_evidence.py
```

The regression invokes the real legacy-capture, roadmap and token-detector
verifiers through the runner. On the baseline all three fail at the repository
root assertion; direct documented invocations pass. With the correction all
three runner invocations pass. Additional subprocess controls exercise all four
registered interfaces, packet-relative working directories, unchanged nonzero
exit status, and unregistered or outside paths with a registered basename.

The source-manifest packet reaches its independent existing failure after the
invocation repair: its archived observation requires 65 inputs, while current
Pump sources have at least 67 Rust/Cargo inputs. That historical source drift is
not repaired or treated as passing here (separate pending PR #1363). The three
positive packets use unchanged original inputs and saved observations.

Validation: three focused tests, ten root tooling tests and all nine capture
checks pass. The focused suite is included in evidence CI. Use a checkout that
preserves the historical packets' Git bytes; checkout newline conversion is a
separate issue. This does not run the entire research tree, build programs,
execute contracts, establish source equivalence, or change overall pass/fail
aggregation. Pending PR #1362 addresses aggregation; #1382 addresses publication
and output discovery. Neither is implemented by this invocation correction.
