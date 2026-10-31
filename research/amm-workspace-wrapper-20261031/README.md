# AMM native-build workspace wrapper override

Base: `90300f9d2efe3ef014b116172251a41bfb104d78`.

`native_build.build` removes `RUSTC_WORKSPACE_WRAPPER`, but Cargo also accepts
`CARGO_BUILD_RUSTC_WORKSPACE_WRAPPER`. The latter survives the build environment
and is absent from `cache_inputs.context`. An ambient workspace wrapper can
therefore change compilation without changing the attempt's admitted inputs.

The [Cargo environment reference](https://doc.rust-lang.org/cargo/reference/environment-variables.html)
documents both the configuration alias and the nesting order:
the root wrapper receives the workspace wrapper as its compiler argument.

## Real host compiler reproduction

Run the retained probe against either checkout with an installed official host
Cargo/rustc directory (no installer or network access is used by the probe):

```sh
python research/amm-workspace-wrapper-20261031/probe.py /path/to/checkout /path/to/rust/bin
```

The probe compiles and executes a dependency-free Rust crate twice using the
production AMM environment construction and generated root wrapper. The ambient
workspace wrapper adds one `--cfg` flag. On the base, the probe executes the
unchanged environment-construction statements extracted from `build`'s AST;
with the fix it calls the extracted production helper. Neither route fabricates
compiler results. Both builds share identical source and lockfile contents.

| Checkout | Clean executable | Ambient-wrapper executable | Cache context within pair |
| --- | --- | --- | --- |
| Base | `false` | `true` | identical |
| Fixed | `false` | `false` | identical |

Full source/context hashes and compiler versions are retained in `before.json`
and `after.json`. The context hash changes between checkouts because the builder
implementation is itself hashed; the defect is equality *within* the base pair.

Recorded execution: macOS arm64, CPython 3.12.13, official rustc
`1.99.1 (58cf8f9c3 2026-10-13)` and Cargo `1.99.1 (5f94df478 2026-08-27)`.
`toolchain-components.json` retains official distribution URLs and verified
SHA-256 values for rustc, Cargo and the matching host standard library.

## Validation and limits

`tests/test_amm_build_environment.py` tests both spellings and runs actual Cargo
when host Cargo/rustc are available on PATH. `PUMP_TEST_RUST_BIN` selects an
explicit installation. The test is invoked by the verification workflow.
The 242-test root tooling suite, nine captured-image checks, three native output
preservation tests and five baseline-selection tests also passed locally.

This is a host compiler/environment regression, not a fresh AMM SBF rebuild.
The fixture omits the SBF target and uses a different crate name, avoiding the
platform metadata/linker recipe. No reconstructed program, retained capture,
historical attempt, scoring rule or compiled completion claim changes.
