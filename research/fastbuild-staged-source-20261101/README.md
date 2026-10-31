# Bind the source copy after compilation

Base: `9120883a957d7d9b2cab6140f66fb5bc9e6774d5`.

Fastbuild binds the caller's source and checks its transformed copy before Cargo
runs. It did not recheck that copy afterward. A build script writing generated
Rust into `src/generated.rs` therefore returned `ok=true` and published an ELF
while the source receipt described the old bytes, or omitted the new file. The
caller tree stayed unchanged, so the paired-build caller check also cannot see
this mutation of the private compile tree.

`probe.py` exercises the production `fastbuild.build` API, real rsync, Cargo,
rustc, rust-lld and llvm-objcopy with five tiny dependency-free Rust fixtures.
Only the SDK/recipe and lock directory are pointed at isolated installed tools.
There are no substituted compiler results or captured program inputs.

| Case | Before | After |
| --- | --- | --- |
| Unchanged source returning 1 | publishes A | publishes A |
| build.rs rewrites recorded generated source to return 2 | publishes B with stale source receipt | rejects before publication |
| build.rs creates previously absent generated source returning 2 | publishes B with incomplete source receipt | rejects before publication |
| Generated Rust in `OUT_DIR`, ordinary output in crate-root `target` | publishes B | publishes B |
| Pre-generated source returning 2, no mutation | publishes B | publishes B |

The complete stripped ELF hashes are:

- A: `115275272733f68b49f6b74f175efd97ef9821fd3ed592d8186e4bdfc98243af`
- B: `8ada743c90a292ea69a7a0a8fa15afef29ea5bf3c517e06017e1f7d95dec9b59`

Both source-changing cases now raise
`source inputs changed during compilation: src/generated.rs` after Cargo exits
successfully, before either binary is installed. The build log and initial
receipt remain available. The correction snapshots the transformed crate after
staging and checks it again before successful publication; existing compiler
failure and stack-diagnostic paths remain unchanged. `assert_unchanged` accepts
an optional phase label, preserving the existing staging diagnostic by default.

The standard generation control follows Cargo's documented
[build-script output directory](https://doc.rust-lang.org/cargo/reference/build-scripts.html#outputs-of-the-build-script).
The test also exercises the existing crate-root `target` exclusion.

Reproduce with Python 3.12 and an already installed official macOS arm64 v1.44
platform-tools SDK (rustc 1.79.0-dev, Cargo 1.79.0). The retained official archive
SHA-256 is `66e20d135fddd70ff519baf7ff320d762957f9aedf93a50e23756db23ad79351`.

```sh
python -B research/fastbuild-staged-source-20261101/probe.py "$PWD" /path/to/platform-tools
PUMP_BUILD_TEST_SDK=/path/to/platform-tools python -B tests/test_fastbuild_staged_source.py
```

`results.json` retains the same five workflows before and after. The two-method
regression passes with the real SDK enabled; its always-available publication
control uses real rsync and a substituted compiler boundary to verify archived
prior binaries, logs, receipt retention and lock release. The complete compiler
evidence comes from the actual SDK probe. Existing `contract-tests` CI discovers
the module; the actual SDK test is explicitly optional where tools are absent.
Affected checks: 50 fastbuild methods (45 pass, 5 optional skips), 25 source
methods (22 pass, 3 platform skips), 12 staging tests, 250 tooling tests and all
9 retained captures pass.

This is an ordinary build receipt correction. It does not prove a maintained
program rebuild, full reproducibility, or runtime equivalence. The check covers
the staged crate's existing source-input contract, not the whole environment or
toolchain. A transient rewrite restored before the final comparison is outside
this before/after check. Historical evidence is unchanged.
