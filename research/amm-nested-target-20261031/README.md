# Preserve nested Rust target modules in AMM staging

Base: `90300f9d2efe3ef014b116172251a41bfb104d78`.

The AMM workspace recipe treats every directory named `target` as generated
output. A valid `src/target/mod.rs` is therefore omitted from the main crate,
rejected in the local dependency, and ignored by the staged inventory. The
native builder's unanchored rsync exclusion also prevents resetting an existing
nested target directory between attempts.

The retained probe adds a normal `mod target` to the existing authored staging
fixture, then uses real Cargo/rustc before and after the production recipe:

```sh
python research/amm-nested-target-20261031/probe.py /path/to/checkout /path/to/rust/bin
```

| Checkout | Original host build | Stager verdict | Staged host build |
| --- | --- | --- | --- |
| Base | exit 0 | `verified: true`, module absent | exit 101, E0583 |
| Fixed | exit 0 | `verified: true`, module present and hashed | exit 0 |

`before.json` and `after.json` retain the reports and compiler diagnostics.
The same host compiler was used for both: official macOS arm64 rustc
`1.99.1 (58cf8f9c3 2026-10-13)`, Cargo `1.99.1 (5f94df478 2026-08-27)`,
with CPython 3.12.13. Builds are offline and use no registry dependencies.

`tests/test_amm_nested_target.py` additionally runs real lane staging up to an
intentionally absent compiler boundary. Before the fix, an attempt's changed
module and extra file survive the reset. Afterward the baseline bytes return
and the extra file disappears. No compiler success is simulated in that test.
The test also checks both crate inventories and keeps generated crate-root
target contents excluded. Its real host Cargo check runs when Cargo/rustc are
on PATH, or when selected through `PUMP_TEST_RUST_BIN`.
The known vendored Pubkey crate's root `target` remains excluded as well, while
its `src/target` source module is retained and hashed.

Only tooling and authored fixtures change. This does not rebuild the maintained
AMM SBF program or claim improved byte equality or runtime coverage.
