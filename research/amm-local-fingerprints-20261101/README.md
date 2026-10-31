# Native AMM local Cargo fingerprints

Base: `9120883a957d7d9b2cab6140f66fb5bc9e6774d5`.

The native builder promises to rebuild both local crates after restoring source. It previously touched their Rust files with the local wall clock. A retained warm target dated ahead of that clock still makes those files look older than Cargo's fingerprints. Cargo reports both packages as fresh and keeps the previous compiled behavior.

`probe.py` creates a dependency-free two-package Cargo workspace using the builder's two local package names and paths. It builds `native_transfer_fee::value() == 1`, dates the retained fingerprint files one hour ahead, changes the function to return 2, and executes the production invalidation code before another real offline Cargo build. The base implementation is extracted unchanged from `native_build.build`; the fixed implementation is the production `invalidate_local_crates` helper. No compiler, artifact, or freshness result is mocked.

Using the authenticated official platform-tools v1.44 macOS compiler (`rustc 1.79.0-dev`, Cargo `1.79.0 (804e32543 2025-01-29)`), the base executable still prints `1` and Cargo says `Fresh` for both local packages. With explicit local fingerprint invalidation, Cargo recompiles both and the executable prints `2`. `results.json` retains those outputs without local path details. The official archive SHA256 is `66e20d135fddd70ff519baf7ff320d762957f9aedf93a50e23756db23ad79351`; its full repository inventory was verified before use.

```sh
python -B research/amm-local-fingerprints-20261101/probe.py "$PWD" /path/to/platform-tools
PUMP_TEST_RUST_BIN=/path/to/platform-tools/rust/bin python -B tests/test_amm_native_fingerprints.py
```

The correction removes only the two local packages' host and target release fingerprint directories, keeping external artifacts and fingerprints. It does not depend on a particular clock or source-file timestamp. Regression tests exercise real Cargo with implicit and explicit host targets, changing both main and dependency source; the rebuilt executable must print `12`. An independent preservation test retains unrelated dependency cache files. The test discovers Cargo/rustc on PATH or accepts `PUMP_TEST_RUST_BIN` and is wired into CI.

Both tests passed with the pinned v1.44 tools and official host Rust/Cargo 1.99.1. Nine existing lane tests, three native-output preservation tests, 250 tooling tests, and all nine evidence captures passed. This is a local Cargo freshness proof using host executables, not a native AMM/SBF reconstruction or whole-ELF equivalence claim. No maintained program source or original capture changes.
