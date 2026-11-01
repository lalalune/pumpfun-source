# Local-only prepared caches and the supported builder

Base: `599891304e83e853ec723dc1417550bef4e1c074`.

`prepare_locked_cargo_home.py` advertises an isolated offline Cargo cache and
already accepts lockfiles containing only local packages. However, that path
publishes only `cache-manifest.json`. The supported v1.53/v1.54 builder requires
and copies a `registry/` directory, so it rejects the successfully prepared
cache with `an existing offline registry cache outside output is required`.
Adding only an empty `registry/` makes the same cache usable by that builder.

This is producer/consumer interoperability, **not** a claim that ordinary Cargo
rejects the cache. No explicit documentation pairing these two commands was
found. Both are maintained build tools, and the preparer's CLI and README do
not exclude zero-registry lockfiles. The existing local-only test explicitly
accepts them without any source Cargo home.

The correction creates `registry/` inside the private staging directory before
publication. Registry package selection, config requirements, copied file
bytes, manifest hashes, atomic no-replace publication and cleanup stay the
same. The existing path-only regression now requires an empty output registry
while proving the absent source Cargo home is still never created.

This follows espressoamer-sudo's [#784](https://github.com/lalalune/pumpfun-source/pull/784), which
made local-only caches independent of source registry state. That requirement
is preserved: no source registry/configuration is read for these lockfiles,
the package list remains empty, and the config digest remains null. Only the
output directory layout changes.

## Actual workflow

`probe.py` uses the installed official Darwin arm64 v1.53 SDK. Cargo generates
each lockfile offline; the actual preparation CLI produces its cache, then the
unchanged exact-base supported builder plans and builds a tiny generic crate.
Two cases cover no dependencies and a local path dependency. A separate control
uses the same prepared file bytes with an explicitly created empty registry.
Both control builds work on base; both prepared-cache builds are rejected.
After correction, both prepared-cache builds succeed with the identical
stripped hashes as their controls. No resulting image is executed.
Separate direct Cargo builds accept the originally prepared layout on both
revisions and produce those same hashes: plain Cargo already worked.

The proof also prepares a nonempty cache from the repository's real retained
Inflector 0.11.4 archive/index, and checks missing-archive, unsupported-registry
and occupied-output refusals. Every prepared file hash and complete manifest
is identical across revisions, including the nonempty cache. All source cache
and caller source files are preserved. The nonempty archive control establishes
cache selection/publication, not a complete Inflector dependency build.

```sh
python -B research/empty-registry-cache-20261101/probe.py \
  --repo . --tools /path/to/solana-cache \
  --revision 599891304e83e853ec723dc1417550bef4e1c074 \
  --expect base --output /tmp/empty-cache-before.json
python -B research/empty-registry-cache-20261101/probe.py \
  --repo . --tools /path/to/solana-cache \
  --expect fixed --output /tmp/empty-cache-after.json
PUMP_SUPPORTED_TEST_TOOLS=/path/to/solana-cache \
  python -B scripts/test_prepare_locked_cargo_home.py
```

The cache path must already contain the policy-authenticated v1.53 SDK and
pinned v1.52 `llvm-objcopy`. No downloads, global installation or user Cargo
home inspection are performed. The SDK reports rustc 1.89.0-dev, LLVM 20.1.7
and Cargo 1.89.0. `results.json` records the stable observations and exact tool
identities; full probe output additionally retains compiler logs. Per revision
there are two Cargo lockfile generations and six preparation CLI invocations;
the base executes four builds, the correction six builds (including two
direct Cargo builds on each revision).

An additional integration run selected the supported consumer at
`7fd3fe422d920ec3cef8eb138791d70a1bd2acdc` with `--consumer-revision`.
It includes the subsequently merged explicit-directory correction (#3910).
Both prepared-cache builds still pass with exactly the same candidate hashes;
the producer, policy and source inventory inputs are unchanged on that main.

The existing CI command runs the updated local-only regression. The added full
SDK regression runs when `PUMP_SUPPORTED_TEST_TOOLS` points to a qualified
Darwin cache, and explicitly skips otherwise. The public proof does not run a
compiled image, VM, native model or protocol. A retained reference image is
read solely for the supported builder's required postcompile byte comparison;
there is no reconstruction or equivalence claim. The mandatory unchanged
tooling suite includes its existing LiteSVM fixtures.

Validation passed: all 18 cache regression methods, three admission methods,
two long-output methods, the required 253 tooling tests and all nine capture
checks. One existing Cargo-metadata method initially skipped because Cargo
was not on `PATH`; it was separately rerun with the qualified host Cargo and
passed. The SDK regression ran without skipping. No SDK v1.54 build is claimed.
