# Respect compiler-declared environment dependencies in direct cache reuse

`DependencyCache.compile_main` obtains a fresh Cargo plan, restores cached external
rlibs, and invokes only the main compiler. Cargo's normal dependency invalidation
does not run. A registry dependency using `env!` or `option_env!` can therefore
retain old compiled values when the caller changes or removes a consumed variable.
The cache key binds flags/profile overrides but not these compiler-declared inputs.

Read the hash-verified cached rustc dep-info and compare each declared binding with
the corresponding fresh Cargo unit's effective environment, including Cargo's own
package metadata. On a changed binding or unavailable dependency information, run
the normal locked, offline Cargo build and report cache status `bypass`. Unchanged
bindings retain direct reuse. Diagnostics retain variable names, never their values
or unrelated environment entries. The old immutable entry is preserved: callers
using different bindings continue to rebuild unless they use a separately populated
cache. This deliberately favors correctness without replacing historical artifacts.

Rust's [1.79 dep-info writer](https://github.com/rust-lang/rust/blob/1.79.0/compiler/rustc_interface/src/passes.rs)
records missing values separately from empty values and escapes newline, carriage
return and backslash. The parser follows that format, including Unicode characters
that Python's broader `splitlines` would otherwise misinterpret as record breaks.

## Actual SBF proof

```sh
python -B research/dependency-cache-env-20261101/probe.py <repository> <v1.44-macos-sdk>
PUMP_BUILD_TEST_SDK=<v1.44-macos-sdk> PUMP_TEST_RUST_BIN=<host-rust-bin> python -B tests/test_dependency_cache_environment.py
```

The same 11-build probe runs the actual verified-builder CLI, official v1.44
Cargo/rustc, physical source wrapper, SBF linker and objcopy on base
`9120883a957d7d9b2cab6140f66fb5bc9e6774d5` and the fix. It authors a tiny no-std
main crate plus a registry-style fixture supplied through Cargo's directory-source
replacement. No compiler, artifact, plan, cache result or registry service is mocked.
All compilation is offline; the source/config/cache/output trees are temporary and
removed afterwards, and the authenticated SDK stays unchanged. This does not claim
that the synthetic fixture is a published crates.io package.

Before: changing the dependency's consumed value, setting an absent optional value
to empty, using an escaped value, and removing a required value all report successful
cache hits with the old A ELF. Fresh-control builds produce different ELFs. After:
changed bindings use ordinary Cargo and match their fresh-control ELFs; a missing
required value fails compilation and produces no successful comparison report.
Intact repeats, an unrelated environment change, Cargo-injected package metadata,
and an escaped-value repeat still hit. Exact statuses and hashes are in `results.json`.

Three new tests passed, including real rustc dep-info emission with escaped Unicode
values and the full SBF probe. Existing cache discovery ran 15 tests (13 passed,
2 optional compiler tests skipped there and executed separately); 4 Cargo-log tests,
2 verified-build optimization tests, 3 seed-override tests, 250 tooling tests and
9 captured-evidence checks passed. CI's contract-tests job discovers the new module;
its real rustc test runs when rustc is available and the SBF probe requires the SDK
variable above.

Scope: compiler-declared `env!`/`option_env!` dependencies of cached external units.
This is not a hermetic closure claim for arbitrary build scripts, a maintained Pump
rebuild, a matching gain, or equivalence to the original program. Program sources,
retained captures, scoring rules and unrelated process environment are unchanged.
