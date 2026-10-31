# Verified workspace manifest table boundaries

`pump_build_verified.py --workspace-layout` used substring searches to separate
package metadata, the release profile, and the empty workspace table. A legal
comment mentioning `[profile.release]` caused it to move the package table into
the generated workspace manifest and leave an invalid crate manifest. Header-like
lines in multiline package descriptions and a comment after `[workspace]` also
failed admission. This is the verified builder entrypoint; the earlier fix in
[PR 2371](https://github.com/lalalune/pumpfun-source/pull/2371) covered fastbuild.

Find standalone literal headers only after a complete TOML prefix, and validate
the final workspace slice as TOML. Slice the original text so package metadata
and release settings remain intact. The same release-only, final-empty-workspace
restriction still applies. The maintained Pump manifest produces byte-identical
staged manifests before and after this change.

## Actual compiler reproduction

```sh
python -B research/verified-workspace-manifest-tables-20261101/probe.py <repository> <v1.44-macos-sdk>
PUMP_BUILD_TEST_SDK=<v1.44-macos-sdk> python -B tests/test_verified_workspace_manifest_tables.py
```

The same probe runs the real verified-build CLI, official v1.44 Cargo/rustc, its
physical source wrapper, the SBF linker, and objcopy on four tiny no-std fixtures.
No compiler, manifest parser, artifact or result is mocked. Cargo runs offline
with an empty isolated registry. The fixture/output tree is temporary and removed
after each run; the authenticated SDK remains unchanged. Provenance is retained
in `results.json`.

On base `9120883a957d7d9b2cab6140f66fb5bc9e6774d5`, the plain fixture builds and
all three comment/string variants fail. After the fix, all four build with
`source_unchanged=true` and the same candidate ELF SHA-256:
`7afbdfc8e467da02750384ee8f38a92dfbbc1876472ad19aa511a1a8c60837a1`.
This equality is between these tiny compiler fixtures, not against the original
Pump program. No matching gain or full reconstruction is claimed.

Five regression tests passed, including actual Cargo metadata admission on the
original/staged variants, the real SBF builds, original-manifest byte identity,
and continued rejection of unsupported layouts. CI's existing `contract-tests`
job discovers the new test module; Cargo metadata runs when Cargo is installed,
and the macOS SBF probe runs when `PUMP_BUILD_TEST_SDK` is supplied. Required
250 tooling tests and 9 captures passed, plus 2 verified-build optimization tests
and 3 seed-override tests. Program sources and retained captures are unchanged.
